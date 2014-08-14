#!/usr/bin/env python
import sqlite3
import pylab
import numpy
import datetime
import matplotlib.cm as cm
dbname = "test.db"

def gettimeseries( tablename, key ):
    con = sqlite3.connect(dbname,detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
#    statement = 'select TT as "TT [timestamp]", %s from %s where TT<"2014-01-001"' % ( key, tablename )
    statement = 'select TT as "TT [timestamp]", %s from %s' % ( key, tablename )
    cur.execute(statement)
    data = cur.fetchall()
    cur.close()

    return data

def plottimeseries( tablename, key ):
    data = gettimeseries( tablename, key ) 
    pylab.plot_date([x["TT"]for x in data],[x[key]for x in data],".")
    pylab.show()

def nextmonth( thismonth ):
    if thismonth.month == 12:
	thismonth = datetime.datetime(year=thismonth.year+1,month=1,day=1)
    else:
	thismonth = datetime.datetime(year=thismonth.year,month=thismonth.month+1,day=1)
    return thismonth

def plothist( tablename, key ):
    con = sqlite3.connect(dbname,detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # date range process
    statement = 'select min(TT) as "TT [timestamp]", max(TT) as "TT [timestamp]" from %s' % ( tablename )
    cur.execute(statement)
    mindate, maxdate = cur.fetchone()
    minmonth = datetime.datetime(year=mindate.year,month=mindate.month,day=1)
    maxmonth = datetime.datetime(year=maxdate.year,month=maxdate.month+1,day=1)

    # actual process
    thismonth = minmonth
    i=0
    while thismonth<maxmonth:
	print thismonth,nextmonth(thismonth)
	statement = 'select TT as "TT [timestamp]", %s/10. as %s from %s where TT>"%s" and TT<"%s"' \
	    % ( key, key, tablename, thismonth.date(), nextmonth(thismonth).date() )
	cur.execute(statement)
	data = cur.fetchall()
	
	hist, bin_edges = numpy.histogram([x[key] for x in data],bins=40,range=(0,40),normed=True)
	pylab.plot(bin_edges[:-1]+0.5,numpy.cumsum(hist),label=thismonth.strftime("%y/%m"),color=cm.spectral(float(thismonth.month)/ 12))
	thismonth=nextmonth(thismonth)
	i+=1

    cur.close()
    pylab.ylabel("Cumulative Probability")
    pylab.xlabel("%s [m/s]" % key)
    pylab.grid()
    pylab.legend(loc="lower right")
    pylab.title(tablename)
    pylab.savefig("%s-%s.png" % (key, tablename) )
    pylab.clf()

def main():
    plothist( "T0001", "AFMX" ) # AFMX is max velocity
    plothist( "T0002", "AFMX" ) # AFMX is max velocity
    plothist( "T0001", "ABMX" ) # AFMX is max velocity
    plothist( "T0002", "ABMX" ) # AFMX is max velocity

if __name__ == "__main__":
    main()

