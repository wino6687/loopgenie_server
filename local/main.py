import random
import dbConn
from tripopt import RouteOptimizer

import shapely.wkb as wkb

from shapely.geometry import MultiLineString, Point
from shapely import ops
import itertools
import networkx as nx
import os
import json
import numpy as np
import requests
import geocoder
import config


global km_to_degree 
global snap_tolerance 
km_to_degree   = 111
snap_tolerance = 1e-4


# TODO
    # * Select only the longest "duplicate" trail
    # * Database side of tool
    # * Integrate location so it uses a location and DB results rather than a folder
    # * Geospatial database to hold tracks
    # * Download and add tracks if not downloaded
    # * Subset to use data in location
    # * add campground/land-type layer (http://www.ultimatecampgrounds.com/index.php/products/full-map)
    # http://www.uscampgrounds.info/

                  
class Track():
    def __init__(self, filename):
        self.name             = None
        self.track            = None
        self.points           = None
        self.connected_tracks = {}
        self.node_dict        = {}
        self.paths            = {}
        self.filename         = filename
        
        self.parse_hex(filename)  
    
    def parse_hex(self, trail): 
        geom = wkb.loads(trail[1], hex=True)
        xy = geom.xy
        self.points = []
        for i in range(len(geom.xy[0])):
            self.points.append((xy[0][i],xy[1][i]))
        self.name = trail[0]
        self.track = self.check_track(geom)
        
        
    def check_track(self, track):
        """
        Sometime track GPX files are effectively doubled -- tracks are there and back,
        rather than just 1-way segments.  This method returns only the 1-way segment
        for the track
        """
        mp        = track.length/2
        mp        = Point(track.interpolate(mp))
        new_track = ops.snap(track, mp, snap_tolerance)
        if not new_track.contains(mp):
            print("Unable to snap track")
            return track
        result    = ops.split(new_track, mp)  
              
        result[0].intersects(result[1])
        isect = result[0].intersection(result[1])
        
        if isect.type == "Point":
            return track
            
        if len(isect)/(len(result[0].coords)-1) > .5:
            return result[0]
        else:
            return track
                
    def get_nodes(self):
        if self.paths:
            return self.paths
        else:
            self.generate_nodes()    

    def track_intersection(self, track2, tolerance=0.1):
        """ Returns the latitue and longitude where track2 intercepts track1 (self)"""
        if not isinstance(track2, Track):
            raise Exception("Track 2 is not a valid Track")
            
        track2_shape = track2.track
        track1_shape = self.track
        try:
            trk_dist = track1_shape.distance(track2_shape)*km_to_degree
        except:
            pass
            #raise Exception("Unable to measure distance between %s and %s" % (self.filename, track2.filename))
        if trk_dist < tolerance: # we can connect these tracks
            line1, line2 = ops.nearest_points(track1_shape, track2_shape)
        
            node    = (line1.x, line1.y)
    
            self.connect_track(track2, node)
            return (node)
            
        return False
    
    def connect_track(self, track2, node):
        """
        Add connections between a second track and a node 
        from an existing track

        Parameters:
        -----------
        track2: Track() 
            second track to add connection to
        node: (POINT.x,POINT.y)
            tuple of shapely point coords of nearest node to track2
        """
        self.connected_tracks[track2.name] = Point(node)
        track2.connected_tracks[self.name] = Point(node)
    
    def generate_nodes(self):
        """
        Returns a dictionary with a node id corresponding
        to the distance along the track, and a given node Point.
        """
        points = self.points[0]
        if not self.node_dict:
            
            node_dict          = {}
            length             = self.track.length
            node_dict[0]       = self.track.interpolate(0)
            node_dict[length]  = self.track.interpolate(length)
            
            for key in self.connected_tracks:
                node_pt             = self.connected_tracks[key]
                node_pos            = self.track.project(node_pt)
                if self.check_precision(node_pos, node_dict):
                    # There is a tolerance issue with establishing nodes.
                    # Shapely is unable to snap nodes with enough percision
                    # To create meaningful segments. 
                    node_dict[node_pos] = node_pt

            self.node_dict = node_dict
            
        return self.node_dict
        
    def check_precision(self, value, dictionary):
        for key in dictionary.keys():
            if  abs(value - key) < snap_tolerance:
                return False
        
        return True
        
    def split_track(self, track, point):
        # Snap Point
        new_track  = ops.snap(track, point, snap_tolerance)
        
        while not new_track.contains(point):
            if new_track.project(point) == 0:
                # The split has a tolerance issue with the prior track.
                # We therefore create a new mini-trail, and let the old
                # trail be carried forward.
                print("Making mini segment at %s" % str(point))
                point = new_track.interpolate(snap_tolerance*1.1)
            # Use the nearest point functionality to try and estimate a suitable node point on the line
            point, __ = ops.nearest_points(track, point)
            new_track = ops.snap(track, point, snap_tolerance)
            if not new_track.contains(point):
                raise Exception("Unable to snap %s to track at %f" % (str(point),snap_tolerance))
            
        result = ops.split(new_track, point)
        
        if len(result) == 1:
            return(result[0], None)
            
        return (result[0], result[1])
            
    def setup_paths(self):
        """
        Splits the track at each node to generate
        a set of line segments that make up the path
        """
        working_path = self.track
        nodes        = self.generate_nodes()
        node_place   = [x for x in nodes]
        node_place.sort()
        
        for i, dist in enumerate(node_place):
            node = nodes[dist]
            if i == 0:
                continue
            origin      = nodes[node_place[i-1]]
            destination = nodes[node_place[i]]    
            path_name = "%i_%i_%s" % (i-1,i, self.name)
            if i < len(node_place)-1:
                # The last point in the track, therefore it can't be split
                try:
                    path_pts, working_path = self.split_track(working_path, node)
                except:
                    # This was previously an exception, but sometimes paths are dumb.
                    # I don't know the best way to kick the path forward, or to remove it.
                    print("Unable to split track for %s" % path_name)
                    path_pts = working_path
            else:
                path_pts = working_path

            try:
                path = Path(path_name, path_pts, origin.coords[0], destination.coords[0])
                self.paths[path_name] = path
            except:
                raise Exception("Unable to add path to class on:%s" % self.name, i,"of ", len(node_place)-1)
    

class Path():
    paths = {}
    def __init__(self, name, points, origin, destination):
        self.name         = name
        self.points       = points
        self.origin       = origin
        self.destination  = destination
        self.distance     = points.length*km_to_degree
        self.original_key = (origin, destination, name)
        self.reverse_key  = (destination, origin, name)
        self.db_hash      = self.make_hash(origin, destination, name)


        self.add_self()
        
    def __new__(cls, grouping, points, origin, destination):
        hashdat = cls.make_hash(origin, destination, grouping)
        chk = cls.get(hashdat)
        if chk:                      # already added, just return previous instance
            return chk
        cls
        self = object.__new__(cls)   # create a new uninitialized instance
        self.__init__(grouping, points, origin, destination)
        return self                  # return the new registered instance           
            
    @classmethod
    def list_paths(cls):
        return cls.paths
            
    def add_self(self):
        """
        Hash path object into paths dict. Update if exists already.
        """
        self.path_distance()
        if self.db_hash not in self.paths: 
            Path.paths[self.db_hash] = self
        else:
            old_path = self.get(self.db_hash)
            
            if self.points != old_path.points:
                del self.paths[self.db_hash]
                self.add_self(self)
            else:
                self = old_path
    
    @classmethod   
    def make_hash(cls, node1, node2, grouping):
        """
        Make ordered tuple of ndoes for hashing 
        """
        ordered   = [node1, node2]
        ordered.sort()
        ordered.append(grouping)
        return(tuple(ordered))

    @classmethod    
    def get(cls, db_hash):
        hash_value = cls.make_hash(db_hash[0], db_hash[1], db_hash[2])
        try:
            return cls.paths[hash_value]
        except:
            return False
    
    @classmethod
    def lookup_path(cls, db_hash):
       path = cls.get(db_hash)
       if path:
        return (path.original, path.distance)
        
    @classmethod
    def get_distance(cls, db_hash):
        path = cls.get(db_hash)
        if path.original_key == (db_hash[0], db_hash[1], db_hash[2]):
            return path.distance
        else:
            return -path.distance
    
    def path_distance(self):
        
        return self.distance
        
        
def find_roads():
    """ Find nearest road to track """
    pass

class TripPlanner():
    def __init__(self, trails, location=""):
        """
        Will setup a new trip for a specific location.
        The trip will load all tracks, connect them together, and generate
        the path and trail network for optimization.
        """
        self.tracks        = {}
        self.nodes         = []
        self.location      = location
        self.file_list = trails # load trails into class (should rename to 'trail_list')
        self.trail_network = nx.Graph()

        self.load_all_tracks()
        self.connect_tracks()

    
    def load_all_tracks(self): # we need to take geoJSON and not GPX now
        if self.tracks:
            return self.tracks
            
        for geoj in self.file_list: # this is going to loop through ('trail_name', 'hex value of geometry')
            try: # only valid trails can be returned from mongo, so maybe don't need this anymore
                geotrack = Track(geoj) # track takes filename 
                self.tracks[geotrack.name] = geotrack
            except Exception as e:# this is a dated exception with PostGIS db
                print(e)
                raise Exception("Could not load track %s" % geoj[1]['properties']['name'])        
        return self.tracks

            
    def connect_tracks(self):
        """
        Joins tracks together.  Track connectivity is established within 100 meters
        """
        print("Joining %i tracks together..." % len(self.file_list))
        for line1, line2 in itertools.combinations(self.tracks.values(),2):
            line1.track_intersection(line2)
                    
    def random(self):
        track_id = random.choice(list(self.tracks.keys()))
        return self.tracks[track_id] 
    
    def list_connectivity(self):
        all_connections = {}
        for track_key in self.tracks:
            track = self.tracks[track_key]
            all_connections[track.gpx.name] = track.connected_tracks
        
        return all_connections
   
    def create_network(self):
        """
        Will go through track connectivity and create a network
        of nodes and edges for the entire network of trails
        """
        for track in self.tracks.values():
            if not track.paths:
                track.setup_paths()
            for key in track.paths:
                path = track.paths[key]
                self.trail_network.add_node(path.origin)
                self.trail_network.add_node(path.destination)
                self.trail_network.add_edge(path.origin, path.destination, length=path.distance, name=key) 
               
            
        pass 
    def add_paths(self):
        """
        Creates a simplified, relational path network for the LP problem
        so that trails make sense when solved.
        """
        for key in self.tracks:
            track = self.tracks[key]
            track.setup_paths()
            for node in track.node_dict.values():
                if node not in self.nodes:
                    self.nodes.append(node)            


def LocationName(location):
    url = "https://{}.execute-api.us-east-2.amazonaws.com/Prod/geocode/api/v1/geocode?q={}".format(os.environ['API_DNS'], location)
    response = requests.request("GET", url)
    json = response.json()['items'][0]["position"]
    lat, lon = json['lat'], json['lng']
    return [lat,lon]

def setup_trips(trails, location):
    """
    Instantiate TripPlanner object based on location 
    and create network (called from main)
    """
    trip = TripPlanner(trails, location)
    trip.create_network()
    return trip

def create_trip(trip_db, maxdist=30):
    """
    Instantiate RouteOptimizer based off of trail network created
    by TripPlanner. Solve optimal trip. (called from main)
    """
    opt = RouteOptimizer(trip_db.trail_network, maxdist=maxdist)
    opt.setup_lp()
    opt.set_grouping_constraint(1)
    opt.solve()
    return opt
    
def save_gpx(optimized_network, file_location, gpx_type = "optimization"):
    if gpx_type == "optimization":
        optimized_network.save_gpx(Path, file_location)
    


def run_system(location, distance, tripLength):

    if not location:
        raise Exception("No location has been provided")
        
    if not distance:
        distance = 10
        
    if not tripLength:
        tripLength = 30

    output_location = os.getcwd() + "/saved_trips/{}.gpx".format(location)    
    coords = LocationName(location)
    trails = dbConn.getTrails(coords[1], coords[0], distance*1000)   
    if (trails == []):
        return "No Trails"
    network = setup_trips(trails, location)
    trip = create_trip(network, maxdist = tripLength)
    geojson = trip.save_geojson(Path)
    save_gpx(trip, output_location)
    return geojson

    
    
    
    