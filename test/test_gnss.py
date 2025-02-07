import datetime
import os
import pytest

import pandas as pd

from test import pushd, TEST_DIR
SCENARIO2_DIR = os.path.join(TEST_DIR, "scenario_2")


from RAiDER.gnss.processDelayFiles import (
    addDateTimeToFiles,
    getDateTime,
    concatDelayFiles
)
from RAiDER.gnss.downloadGNSSDelays import (
    get_stats_by_llh, get_station_list, download_tropo_delays, 
    filterToBBox, 
)
from RAiDER.models.customExceptions import NoStationDataFoundError


def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


@pytest.fixture
def temp_file():
    df = pd.DataFrame(
        {
            'ID': ['STAT1', 'STAT2', 'STAT3'],
            'Lat': [15.0, 20., 25.0],
            'Lon': [-100, -90., -85.],
            'totalDelay': [1., 1.5, 2.],
        }
    )
    return df


def test_getDateTime():
    f1 = '20080101T060000'
    f2 = '20080101T560000'
    f3 = '20080101T0600000'
    f4 = '20080101_060000'
    f5 = '2008-01-01T06:00:00'
    assert getDateTime(f1) == datetime.datetime(2008, 1, 1, 6, 0, 0)
    with pytest.raises(ValueError):
        getDateTime(f2)
    assert getDateTime(f3) == datetime.datetime(2008, 1, 1, 6, 0, 0)
    with pytest.raises(AttributeError):
        getDateTime(f4)
    with pytest.raises(AttributeError):
        getDateTime(f5)


def test_addDateTimeToFiles1(tmp_path, temp_file):
    df = temp_file

    with pushd(tmp_path):
        new_name = os.path.join(tmp_path, 'tmp.csv')
        df.to_csv(new_name, index=False)
        addDateTimeToFiles([new_name])
        df = pd.read_csv(new_name)
        assert 'Datetime' not in df.columns


def test_addDateTimeToFiles2(tmp_path, temp_file):
    f1 = '20080101T060000'
    df = temp_file

    with pushd(tmp_path):
        new_name = os.path.join(
            tmp_path,
            'tmp' + f1 + '.csv'
        )
        df.to_csv(new_name, index=False)
        addDateTimeToFiles([new_name])
        df = pd.read_csv(new_name)
        assert 'Datetime' in df.columns


def test_concatDelayFiles(tmp_path, temp_file):
    f1 = '20080101T060000'
    df = temp_file

    with pushd(tmp_path):
        new_name = os.path.join(
            tmp_path,
            'tmp' + f1 + '.csv'
        )
        new_name2 = os.path.join(
            tmp_path,
            'tmp' + f1 + '_2.csv'
        )
        df.to_csv(new_name, index=False)
        df.to_csv(new_name2, index=False)
        file_length = file_len(new_name)
        addDateTimeToFiles([new_name, new_name2])

        out_name = os.path.join(tmp_path, 'out.csv')
        concatDelayFiles(
            [new_name, new_name2],
            outName=out_name
        )
    assert file_len(out_name) == file_length

def test_get_stats_by_llh2():
    stations = get_stats_by_llh(llhBox=[10,18,360-93,360-88])
    assert isinstance(stations, pd.DataFrame)


def test_get_stats_by_llh3():
    with pytest.raises(ValueError):
        get_stats_by_llh(llhBox=[10,18,-93,-88])



def test_get_station_list():
    stations, output_file = get_station_list(stationFile=os.path.join(SCENARIO2_DIR, 'stations.csv'), writeStationFile=False)
    assert isinstance(stations,list)
    assert isinstance(output_file,pd.DataFrame)


def test_download_tropo_delays1():
    with pytest.raises(NotImplementedError):
        download_tropo_delays(stats=['GUAT', 'SLAC', 'CRSE'], years=[2022], gps_repo='dummy_repo')


def test_download_tropo_delays2():
    with pytest.raises(NoStationDataFoundError):
        download_tropo_delays(stats=['dummy_station'], years=[2022])


def test_download_tropo_delays2(tmp_path):
    stations, output_file = get_station_list(stationFile=os.path.join(SCENARIO2_DIR, 'stations.csv'))

    # spot check a couple of stations
    assert 'CAPE' in stations
    assert 'FGNW' in stations
    assert isinstance(output_file, str)

    # try downloading the delays
    download_tropo_delays(stats=stations, years=[2022], writeDir=tmp_path)
    assert True


def test_filterByBBox1():
    _, station_data = get_station_list(stationFile=os.path.join(SCENARIO2_DIR, 'stations.csv'), writeStationFile=False)
    with pytest.raises(ValueError):
        filterToBBox(station_data, llhBox=[34,38,-120,-115])


def test_filterByBBox2():
    _, station_data = get_station_list(stationFile=os.path.join(SCENARIO2_DIR, 'stations.csv'), writeStationFile=False)
    new_data = filterToBBox(station_data, llhBox=[34,38,240,245])
    for stat in ['CAPE','MHMS','NVCO']:
        assert stat not in new_data['ID'].to_list()
    for stat in ['FGNW', 'JPLT', 'NVTP', 'WLHG', 'WORG']:
        assert stat in new_data['ID'].to_list()
