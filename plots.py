#!/home/msj/miniconda3/bin/python3



import matplotlib as mpl
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import datetime
import matplotlib.lines as mlines
import matplotlib.animation as animation

class BasePlot():
    def __init__(self,n=1,m=1):
        #https://xkcd.com/color/rgb/
        self.colors = ['#3778bf','#7bb274','#825f87','#feb308','#59656d']
        mpl.rcParams['axes.prop_cycle'] = mpl.cycler('color',self.colors)
        self.bg_color = '#ffffff'
        self.fg_color = self.colors[1]
        self.fg_color2 = self.colors[0]
        self.fg_color3 = self.colors[3]
        self.fg_color4 = self.colors[2]
        self.ax_color = self.colors[4]
        
        
        
    def title(self,titletext,x=0.02,y=0.98,horizontalalignment='left',**kwargs):
        self.f.suptitle(titletext,x=x,y=y,color=self.ax_color,horizontalalignment=horizontalalignment,**kwargs)

    def tight_layout(self,*args,**kwargs): 
        self.f.tight_layout(rect=[0, 0.03, 1, 0.95],*args,**kwargs) 
        
        
class BusPlot(BasePlot):
    def __init__(self,csvf,start=None,stop=None):

        super().__init__(n=1,m=0)


        
        self.f, self.ax = plt.subplots()


        self.f.patch.set_visible(False)
        self.ax.set_facecolor('k')
        self.ax.axes.get_xaxis().set_visible(False)
        self.ax.axes.get_yaxis().set_visible(False)
 
        self.f.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=None, hspace=None)
    
        self.df = pd.read_csv(csvf)
        self.df.RecordedTime = pd.to_datetime(self.df.RecordedTime)
        

      
    def make_coordsdf(self):

        df = self.df
        idx = pd.date_range(df.RecordedTime.min(),df.RecordedTime.max(),freq='s')
        
        latdf = pd.pivot_table(df,index='RecordedTime',values='Latitude',columns='VehicleNo',aggfunc='first')
        latdf = latdf.reindex(idx)
        latdf_interp = latdf.interpolate(method='time',limit_direction='both')
        
        longdf = pd.pivot_table(df,index='RecordedTime',values='Longitude',columns='VehicleNo',aggfunc='first')
        longdf = longdf.reindex(idx)
        longdf_interp = longdf.interpolate(method='time',limit_direction='both')
        
    
        
        
        self.coordsdf = latdf_interp.combine(longdf_interp,lambda x,y: tuple(zip(y,x)))
        
        self.coordsdf = self.coordsdf.iloc[::20]
        
#         if self.trim:
#             now = datetime.datetime.now()
#             thishour = now.strftime('%Y-%m-%d %H:00:00')
#             thishour = datetime.datetime.strptime(thishour,'%Y-%m-%d %H:%M:%S')
#             lasthour = (now - datetime.timedelta(hours=1)).strftime('%Y-%m-%d %H:00:00')
#             lasthour = datetime.datetime.strptime(lasthour,'%Y-%m-%d %H:%M:%S')
#             self.df = self.df[self.df.RecordedTime>lasthour]
#             #self.df = self.df[self.df.RecordedTime<thishour]
#             self.coordsdf = self.coordsdf[self.coordsdf.index>lasthour]
#             self.coordsdf = self.coordsdf[self.coordsdf.index<thishour]
        
    def trim(self):
        now = datetime.datetime.now()
        thishour = now.strftime('%Y-%m-%d %H:00:00')
        thishour = datetime.datetime.strptime(thishour,'%Y-%m-%d %H:%M:%S')
        lasthour = (now - datetime.timedelta(hours=1)).strftime('%Y-%m-%d %H:00:00')
        lasthour = datetime.datetime.strptime(lasthour,'%Y-%m-%d %H:%M:%S')
        self.df = self.df[self.df.RecordedTime>lasthour]
        #self.df = self.df[self.df.RecordedTime<thishour]
        #self.coordsdf = self.coordsdf[self.coordsdf.index>lasthour]
        #self.coordsdf = self.coordsdf[self.coordsdf.index<thishour]

        
    def make_scatter(self):
        self.make_coordsdf()
        
        
        longs = self.coordsdf.iloc[0].map(lambda x: x[0])
        lats =  self.coordsdf.iloc[0].map(lambda x: x[1])
        
        longmin = -123.3206 #0.7831
        longmax = -122.5374
        latmin = 49.0
        latmax = 49.479576 #0.4796
        self.ax.set_xlim(longmin,longmax)
        self.ax.set_ylim(latmin,latmax)
        
#         W = longmax - longmin
#         H = latmax - latmin
#         h = 3
#         w = h*W/H
#         self.f.set_size_inches(w,h)
#         s = 0.5
#         fontsize = 12
        s = 1
        fontsize = 20
        cmap = 'cool'
    
        self.scatter = self.ax.scatter(longs,lats,s=s,cmap=cmap,c=range(len(self.coordsdf.columns)))
        self.text = self.ax.text(0.55,0.9,str(self.coordsdf.index[0])[:16],size=fontsize,
                                 color='white',alpha=0.4,transform=self.ax.transAxes,horizontalalignment='left')
        
        self.f.savefig('test.png')
        
    def run(self,i):

        longs = self.coordsdf.iloc[i].map(lambda x: x[0])
        lats =  self.coordsdf.iloc[i].map(lambda x: x[1])
        
        self.scatter.set_offsets(list(zip(longs,lats)))
        self.text.set_text(str(self.coordsdf.index[i])[:16])
        
    def make_ani(self,outfile):
        self.make_scatter()
        

        frames=len(self.coordsdf)
        #print(self.coordsdf.index)
        ani = animation.FuncAnimation(self.f, self.run,frames=frames, interval=50)
        ani.save(outfile,writer='imagemagick')  # This works for gifs
        #ani.save(outfile,writer='ffmpeg')  # Need to used ffmpeg for upload to twitter if you make a video
        print(outfile)
        print(f"{datetime.datetime.now()} df.head(1) {self.df.RecordedTime.sort_values().head(1)}")
        print(f"{datetime.datetime.now()} df.tail(1) {self.df.RecordedTime.sort_values().tail(1)}")
        print(f"{datetime.datetime.now()} coordsdf head {self.coordsdf.index[0]}")
        print(f"{datetime.datetime.now()} coordsdf tail {self.coordsdf.index[-1]}")

        
if __name__ == '__main__':
    #plot = BusPlot('hourly_buses.csv',trim=False)
    
    import sys
    plot = BusPlot(sys.argv[1])
    #plot.trim()

    #plot.make_scatter()
    plot.make_ani('anitest.gif')
    
    