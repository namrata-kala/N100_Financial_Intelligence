import pytest
from src.etl.normaliser import normalize_year

def test_normalize_year_valid_mar_yyyy():
    assert normalize_year("Mar 2024") == "2024-03"

def test_normalize_year_valid_dec_yyyy():
    assert normalize_year("Dec 2012") == "2012-12"

def test_normalize_year_valid_yyyy():
    assert normalize_year("2024") == "2024"

def test_normalize_year_lowercase_month():
    assert normalize_year("mar 2024") == "2024-03"

def test_normalize_year_uppercase_month():
    assert normalize_year("MAR 2024") == "2024-03"

def test_normalize_year_none():
    assert normalize_year(None) is None

def test_normalize_year_empty_string():
    assert normalize_year("") == ""

def test_normalize_year_whitespace():
    assert normalize_year("   ") == ""

def test_normalize_year_mar_yy():
    assert normalize_year("Mar-24") == "Mar-24"

def test_normalize_year_dec_yy():
    assert normalize_year("Dec-12") == "Dec-12"

def test_normalize_year_jan():
    assert normalize_year("Jan 2020") == "2020-01"

def test_normalize_year_feb():
    assert normalize_year("Feb 2021") == "2021-02"

def test_normalize_year_apr():
    assert normalize_year("Apr 2019") == "2019-04"

def test_normalize_year_may():
    assert normalize_year("May 2018") == "2018-05"

def test_normalize_year_jun():
    assert normalize_year("Jun 2017") == "2017-06"

def test_normalize_year_jul():
    assert normalize_year("Jul 2016") == "2016-07"

def test_normalize_year_aug():
    assert normalize_year("Aug 2015") == "2015-08"

def test_normalize_year_sep():
    assert normalize_year("Sep 2014") == "2014-09"

def test_normalize_year_oct():
    assert normalize_year("Oct 2013") == "2013-10"

def test_normalize_year_nov():
    assert normalize_year("Nov 2011") == "2011-11"
