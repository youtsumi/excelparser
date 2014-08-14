#!/usr/bin/env python
import numpy
import pylab
import datetime
import scipy
import scipy.fftpack

formatter=lambda x: datetime.datetime.strptime(x,"%Y/%m/%d %H:%M")
vformatter=numpy.vectorize(formatter)


def total_seconds(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6 

def loaddata( filename, col ):
    return numpy.loadtxt( filename ,\
	    skiprows=1,delimiter=",",usecols=(2,col),
	    dtype={ 'names': ("datetime","value") ,\
		    'formats': ("S20","i4")} )


def secondstotimedelta( s ):
    return datetime.timedelta(int(s/3600/24),s%(3600*24))

def makezeropaddata( filename, col ):
    data=loaddata( filename, col )
    start=formatter(data['datetime'][0])
    end=formatter(data['datetime'][-1])
    days=end-start

    padstart = datetime.datetime(start.year,start.month,start.day)
    padend = datetime.datetime(end.year,end.month,end.day+1)
    npad = ((padend-padstart).seconds+(padend-padstart).days*3600*24)/600
    index = [ padstart + secondstotimedelta(i*600) for i in range(npad) ]
    value = numpy.zeros(npad)
    for one in data:
	td=formatter(one["datetime"])-padstart
	value[(td.seconds+td.days*3600*24)/600] = one["value"]

    return index, value

def makezeropaddailydata( filename, col ):
    index,value=makezeropaddata( filename, col )
    offsetin10min=datetime.timedelta(hours=index[0].hour,minutes=index[0].minute)
    offsetinindex=total_seconds(offsetin10min)/60/10
    tmp=numpy.zeros(len(value)+offsetinindex)
    tmp[offsetinindex:]=value
    value=tmp
    timestamp=numpy.array( \
	[ datetime.datetime(2013,12,13)+datetime.timedelta(seconds=(i*10*60)) for i in range(144) ])

    return timestamp,value 

def excludesometime(filename, col, start=7,end=20 ):
    """Not valid for daily because they use sequential data"""
    result = filter(lambda x: (formatter(x[0]).time()<datetime.time(start,00) \
	    or formatter(x[0]).time()>=datetime.time(end,00)),loaddata(filename,col))
    index = map(lambda x: formatter(x[0]), result)
    value = map(lambda x: x[1], result)
    return index, value

def mkgraph( filename, col=4, label="" ):
    data=loaddata( filename, col )
    pylab.plot(vformatter(data['datetime']),data['value'],label=label)

def mkhist( filename, col=4, label="", rrange=(0,300), bins=60, cumulative=True, exclude=False):
    if exclude:
	index, value=excludesometime( filename, col, 7, 20 )
    else:
	data=loaddata( filename, col )
	value=data['value']
    pylab.hist(value,range=rrange,bins=bins,normed=1,\
	histtype='step',cumulative=cumulative,label=label)

def mkdailygraph( filename, col=4, label="" ):
    index, value=makezeropaddailydata( filename, col )

    avg=numpy.array([value[i:-1:144][numpy.where(value[i:-1:144]!=0)].mean() for i in range(144)])
    median=numpy.array([ numpy.median(value[i:-1:144][numpy.where(value[i:-1:144]!=0)]) for i in range(144)])
    std=numpy.array([value[i:-1:144][numpy.where(value[i:-1:144]!=0)].std() for i in range(144)])

    idx=numpy.where(avg!=0.)
    pylab.errorbar(index[idx],avg[idx],std[idx],fmt="o",label=label)
    pylab.plot(index[idx],median[idx],"x",label=label+"median")


def performfft( filename, col=4, label="" ):
    """ perform fft with non-sequential data """
    index, value=makezeropaddata( filename, col )

    freq=scipy.fftpack.fftfreq(len(value), d=10)
    fft=scipy.fftpack.fft(value)
    pylab.plot(freq,fft*fft.conjugate()*freq**2,label=label)
    for m in [24*60, 12*60, 1*60, 30, 20]:
	pylab.annotate("%d" % m,(1./m,1e10/m**2), xytext=(-2,20), \
		xycoords=('data'), textcoords=('offset points'), \
		arrowprops=dict(arrowstyle="->",connectionstyle="arc3,rad=.2") )
#	pylab.axvline(1./m,linestyle="-.")
    pylab.loglog()
#    pylab.plot(freq,1e2*(freq/1e-1)**2)
#    pylab.plot(freq,1e2*(freq/1e-1)**1)
#    pylab.plot(freq,1e2*(freq/1e-1)**0)
    pylab.xlabel("cycle/min")
    pylab.ylabel("f^2 |P(f)|^2")
    
def checkseq( filename, col=4, label="" ):
    data=loaddata( filename, col )
    start=formatter(data['datetime'][0])
    end=formatter(data['datetime'][-1])
    days=end-start
    interval=formatter(data['datetime'][1])-start
    length=total_seconds(days) / total_seconds(interval)
    index=[ start+datetime.timedelta(seconds=i*total_seconds(interval)) for i in range(length+1) ]
    value=numpy.zeros(length+1)
    
    for i, date in enumerate(data['datetime']):
	idx=total_seconds((formatter(date)-start))/total_seconds(interval)
	print i, data['datetime'][i], date, data['value'][i]
	value[idx] = data['value'][i]

    
    pylab.plot(index,value)

    pylab.show()
 

def plottimeserise( ):
    pylab.clf()
    pylab.axes([0.125,0.60,0.775,0.30])
    mkgraph("MT0001.csv",col=4,label="A1")
    mkgraph("MT0002.csv",col=4,label="B4c")
    pylab.ylabel("Wind dir")
    pylab.legend()
    pylab.axes([0.125,0.30,0.775,0.30])
    mkgraph("MT0001.csv",col=5,label="A1")
    mkgraph("MT0002.csv",col=5,label="B4c")
    pylab.ylabel("Wind vel 10 [m/s]")
    pylab.axes([0.125,0.10,0.775,0.20])
    mkgraph("MT0001.csv",col=18,label="A1")
    mkgraph("MT0002.csv",col=18,label="B4c")
    pylab.ylabel("Temp in 10 deg C")
#    pylab.show("TimeSeries.png")
    pylab.savefig("TimeSeries.png")


def plotcumlativehist( ):
    pylab.clf()
#    mkhist("MT0001.csv",col=5,label="Instant A1")  # 5:瞬時風速
#    mkhist("MT0002.csv",col=5,label="Instant B4c")
#    mkhist("MT0001.csv",col=7,label="2min A1")  # 7:2分風速
#    mkhist("MT0002.csv",col=7,label="2min B4c")
#    mkhist("MT0001.csv",col=9,label="10min A1")  # 9:10分風速
#    mkhist("MT0002.csv",col=9,label="10min B4c")
    mkhist("MT0001.csv",col=11,label="Max A1",cumulative=True) # 11: 最大風速
    mkhist("MT0002.csv",col=11,label="Max B4c",cumulative=True)
    mkhist("MT0001.csv",col=11,label="Max A1 (7-20 excl)",cumulative=True,exclude=True) # 11: 最大風速
    mkhist("MT0002.csv",col=11,label="Max B4c (7-20 excl)",cumulative=True,exclude=True)
#    mkhist("MT0001.csv",col=14,label="Max A1",cumulative=True) # 14: another max wind
#    mkhist("MT0002.csv",col=14,label="Max B4c",cumulative=True)
#    mkhist("MT0001.csv",col=14,label="Max A1 (7-20 excl)",cumulative=True,exclude=True) # 14: another max wind
#    mkhist("MT0002.csv",col=14,label="Max B4c (7-20 excl)",cumulative=True,exclude=True)

    pylab.xlabel("Wind vel 10 [m/s]")
    pylab.ylabel("Prob(>v)")
    pylab.legend(loc='lower right')
    pylab.grid()
    pylab.savefig("Hist.png")

def plotdaily( ):
    pylab.clf()
    mkdailygraph("MT0001.csv",col=9,label="A1")
    mkdailygraph("MT0002.csv",col=9,label="B4c")
    pylab.xlabel("Beijing time")
    pylab.ylabel("Wind vel 10 [m/s]")
    pylab.legend(loc='lower left')
    pylab.grid()
    pylab.xticks(pylab.xticks()[0][::2])
    pylab.savefig("Daily.png")

def plotdailydirection( ):
    pylab.clf()
    mkdailygraph("MT0001.csv",col=4,label="A1")
    mkdailygraph("MT0002.csv",col=4,label="B4c")
    pylab.xlabel("Beijing time")
    pylab.ylabel("Wind direction")
    pylab.legend(loc='lower left')
    pylab.grid()
    pylab.xticks(pylab.xticks()[0][::2])
    pylab.savefig("DailyDirection.png")

def plotfft( ):
    pylab.clf()
    performfft("MT0001.csv",col=9,label="A1")
    performfft("MT0002.csv",col=9,label="B4c")
    pylab.legend(loc='upper left')
    pylab.savefig("FFT.png")

def plotwinddirection( ):
    pylab.clf()
#    mkhist("MT0001.csv",col=4,label="Instant A1", rrange=(0,360), cumulative=False)  # 5:瞬時風向
#    mkhist("MT0001.csv",col=6,label="2min A1", rrange=(0,360), cumulative=False)  # 6:2min風向
#    mkhist("MT0001.csv",col=8,label="10min A1", rrange=(0,360), cumulative=False)  # 8:10min風向
    mkhist("MT0001.csv",col=10,label="Max A1", rrange=(0,360), cumulative=False)  # 10:Max風向
    mkhist("MT0002.csv",col=10,label="Max B4c", rrange=(0,360), cumulative=False)  # 10:Max風向
    pylab.xlabel("Wind direction in degree; N=0, E=90")
    pylab.legend(loc='upper right')
    pylab.savefig("Direction.png")
 
if __name__ == "__main__":
    plottimeserise( )
    plotcumlativehist( )
    plotwinddirection( )
    plotdaily()
    plotdailydirection()
    plotfft()
#    checkseq("MT0001.csv",col=4,label="A1")
