#!/usr/bin/env python
import xlrd
import sys
import os
import sqlite3
import datetime

def database( header, body, types ):

    con = sqlite3.connect("test.db")
    cur = con.cursor()

    tablename = body[0][1]

    dbcontent = reduce( lambda x,y: x+", "+y, \
	map( lambda x: "%s %s" % x , \
	    zip(header, types)) )

    statement = '''create table if not exists %s ( %s )''' \
	    % ( tablename,dbcontent )


    cur.execute(statement)

    cur.execute("create unique index if not exists uniquedata on %s('TT')" % tablename)

    for t in body:
	try:
	    statement = 'insert into %s values(%s) ' \
		% ( tablename, \
		    reduce(lambda x, y: x+", "+y, (["?"] * len(types))))
	    cur.execute( statement, t)
	except:
	    print "duplicated", t

    cur.execute("select * from %s" % tablename)
    con.commit()
    cur.close()


def xldate2datetime( xldate ):
    return datetime.datetime( \
	*xlrd.xldate_as_tuple( xldate, 0 )
	)

def process_row(row,loc_date):
    for i in loc_date:
	row[i] = xldate2datetime( row[i] )
    return row

def process_types(row):
    def classify( x ):
	if x == 1:
	    thistype = 'text'
	elif x == 2:
	    thistype = 'real'
	elif x == 3:
	    thistype = 'timestamp'
	return thistype

    return [ classify(x) for x in row ]
	    
    
def process_sheet(sheet):
    # check which cols have xldate (3)
    header=sheet.row_values(0)
    types=process_types(sheet.row_types(1))
    ids=map( lambda x: x[0],
	    filter( lambda x: x[1]==3, \
	    [  (i,v) for i,v in enumerate(sheet.row_types(1)) ])
	)
    body = [ process_row(sheet.row_values(i),ids) for i in range(1,sheet.nrows) ]

    return header, body, types

def main(target):
    if os.path.exists(target) is not True:
	raise

    book=xlrd.open_workbook(target)
    for sheet in book.sheets():
	
	database(*process_sheet(sheet))
	

if __name__ == "__main__":
    main(sys.argv[1])
