# Function Library
# Import necessary libraries
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import shapely
from shapely import plotting
from sklearn.cluster import DBSCAN

def clean_data_points():
    """
    Cleans the input DataFrame by removing rows with NaN values and duplicates.
    Specifically designed for the POI dataset.
    
    Parameters:
        None - Data is loaded from file POI_.
    
    Returns:
        pd.DataFrame: The cleaned DataFrame.
    """
    pois = pd.read_csv('data\POIs\POI_4815075.csv')
    # TO DO: Add more cleaning steps
    return pois
def clean_data_lines(print_line_map: bool = False, print_point_map: bool = False, map_number: int = 0):
    """
    Cleans the input DataFrame by removing appropriate columns and renaming them.
    merges two DataFrames based on 'link_id' and sorts the result by 'ST_NAME'.
    Specifically designed for the POI dataset.
    
    Parameters:
        print_line_map (list): If True, prints the line map for each street name.
        - Default is None.
        print_point_map (list): If True, prints the point map for each street name.
        - Default is None.
    Returns:
        combined_map (pd.DataFrame): The cleaned and combined DataFrame.
        point_map (GeoDataFrame): The cleaned DataFrame with point geometries obtained by top 300
        largest frecuencies of 'ST_NAME'.
        line_map (GeoDataFrame): The cleaned DataFrame with line geometries obtained by top 300
        largest frecuencies of 'ST_NAME'.
    """
    # Load datasets
    names = gpd.read_file('data\STREETS_NAMING_ADDRESSING\SREETS_NAMING_ADDRESSING_4815075.geojson')
    nav = gpd.read_file('data\STREETS_NAV\SREETS_NAV_4815075.geojson')
    # Combine Linestring geometry datasets
    combined_map = pd.merge(nav, names, how='inner', on='link_id')
    combined_map.drop(columns=['geometry_x'], inplace=True)
    combined_map.rename(columns={'geometry_y': 'geometry'}, inplace=True)
    # Sort DataFrame by street name
    combined_map.sort_values(by='ST_NAME', inplace=True)
    # Reset index
    combined_map.reset_index(drop=True, inplace=True)
    map_data = pd.DataFrame(names['ST_NAME'].value_counts())
    map_data['ST_NAME'] = map_data.index
    relevant_streets = map_data[:300][:]
    point_map = gpd.GeoDataFrame()
    line_map = gpd.GeoDataFrame()
    # Point map
    idx = 0
    for i in relevant_streets['ST_NAME']:
        example = names.loc[names["ST_NAME"] == i]
        lst = [point_map, example.geometry.boundary.extract_unique_points()]
        point_map = gpd.GeoDataFrame( pd.concat( lst, ignore_index=True) )
        line_map = gpd.GeoDataFrame( pd.concat( [line_map, example.geometry], ignore_index=True) )
        if print_point_map and idx < map_number:
            example.boundary.plot()
            plt.title(f"Point Map for {i}")
        if print_line_map and idx < map_number:
            example.plot(column = 'link_id')
            plt.title(f"Line Map for {i}")
        idx += 1
    point_map = point_map.rename(columns={point_map.columns[0]: 'geometry'})
    point_map.set_geometry('geometry', inplace=True)
    line_map = line_map.rename(columns={line_map.columns[0]: 'geometry'})
    line_map.set_geometry('geometry', inplace=True)
    return combined_map, point_map, line_map
# Create individual dataset from streets with the same name dataset
def st_nodes_dbscan(point_map, st_name,  eps:float = 0.5, min_samples:int = 1, show:bool = False):
    """
    Returns the labels for each point provided in the geometry column of the point_map GeoDataFrame.
    The labels are generated using the DBSCAN clustering algorithm.
    input:
        point_map: GeoDataFrame
            A GeoDataFrame containing a geometry column with points to be clustered.
        eps: float
            The maximum distance between two samples for one to be considered in the neighborhood of the other.
            Default is 0.5.
        min_samples: int
            The number of samples in a neighborhood for a point to be considered as a core point.
            Default is 5.
        show: bool
            If True, the function will display a scatter plot of the clustered points.
    output:
        list of labels: list
            A list of labels for each point in the geometry column of the point_map GeoDataFrame.
    """
    st_name = st_name
    data = pd.DataFrame(
        {
            'x': [],
            'y': [],
        }
    )
    d = {'x': [], 'y': []}
    for j in point_map['geometry']:
        d['x'].append(j.x)
        d['y'].append(j.y)
    data = pd.DataFrame(d)
    data['x'] = data['x'].astype(float)
    data['y'] = data['y'].astype(float)
    # Clustering
    dbscan = DBSCAN(eps=eps, min_samples=min_samples).fit(data)
    data['cluster'] = dbscan.labels_
    data['cluster'] = data['cluster'].astype('category')
    if(show == True):
        plt.figure(figsize=(10, 10))
        plt.scatter(data['x'], data['y'], c=data['cluster'], s=40)
        plt.title(f"DBSCAN Clustering for {st_name}")
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.show()
    return data['cluster'].tolist()
def get_street_geometries():
    """
    Returns the geometries of the streets in the combined_map DataFrame.
    The geometries are obtained by merging the line_map and point_map DataFrames.
    
    Parameters:
        None - Data is loaded from file POI_.
    
    Returns:
        list: A list of geometries for each street in the combined_map DataFrame.
    """
    # Load datasets
    names = gpd.read_file('data\STREETS_NAMING_ADDRESSING\SREETS_NAMING_ADDRESSING_4815075.geojson')
    nav = gpd.read_file('data\STREETS_NAV\SREETS_NAV_4815075.geojson')

    data_1 = gpd.GeoDataFrame()
    data_2 = gpd.GeoDataFrame()
    data_1['link_id'] = nav['link_id']
    data_1['DIR_TRAVEL'] = nav['DIR_TRAVEL']
    data_2['ST_NAME'] = names['ST_NAME']
    data_2['geometry'] = names['geometry']
    data_2['link_id'] = names['link_id']

    #Preparing variables of interest
    data = pd.merge(data_1, data_2, how='inner', on='link_id')
    data = gpd.GeoDataFrame(data, geometry='geometry')
    #data.set_geometry('geometry', inplace=True)

    # gather streets with common names
    map_data = pd.DataFrame(data['ST_NAME'].value_counts())
    map_data['ST_NAME'] = map_data.index
    relevant_streets = map_data[:300][:]

    # Construct roads databases
    point_map = gpd.GeoDataFrame()
    roads = []
    for i in relevant_streets['ST_NAME']:
        example = data.loc[data["ST_NAME"] == i]
        example['geometry'] = example.geometry.boundary.extract_unique_points()
        point_map = example.explode(column='geometry')
        # Clustering
        labels = st_nodes_dbscan(point_map, i)
        point_map['cluster'] = labels
        n =  len(np.unique(np.array(labels)))
        for j in range(n):
            data_temp = point_map.loc[point_map['cluster'] == j]
            roads.append(data_temp)
    return roads