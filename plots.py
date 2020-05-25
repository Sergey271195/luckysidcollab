import pandas 
import numpy 
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
import datetime

date = [340.0, 90.0, 400.0] 
amount = [datetime.date(2020, 5, 24), datetime.date(2020, 5, 25), datetime.date(2020, 5, 26)]

col_labels = ['Дата', 'Продукты', 'Услуги', 'Техника', 'АЗС', 'Рестораны'] 
aggs1 = ['27-20-2020', 15400.0, 1000.0, 5000.0, 7500.0, 430.0]
aggs2 = ['27-20-2020', 5400.0, 1000.0, 5000.0, 7500.0, 430.0]
aggs3 = ['27-20-2020', 25400.0, 1300.0, 5000.0, 7520.0, 0.0]
aggs4 = ['27-20-2020', 35400.0, 200.0, 5000.0, 7500.0, 40.0]

aggspie = [35400.0, 2000.0, 5000.0, 7500.0, 4000.0]

aggs = []
aggs.append(aggs1)
aggs.append(aggs2)
aggs.append(aggs3)
aggs.append(aggs4)

def createBarPlot():
    plt.bar(labels, aggs)
    plt.savefig('/home/sergey/Desktop/telegram/total.png')

def createPiePlot():
    fig, axs = plt.subplots(1, 2)
    pie = axs[0].pie(aggspie, autopct='%.1f%%', pctdistance = 1.4)
    axs[1].axis('off')
    axs[1].legend(pie[0], col_labels,
          title="Categories",
          loc="center")
    """ ax = fig.add_subplot(111)
    pie = ax.pie(aggspie, labels = aggspie, pctdistance = 1.1)
    ax.axis('equal')
    
    ax2 = fig.add_subplot(112)
    ax2.axis('off')
    ax2.legend(pie[0], col_labels,
          title="Categories",
          loc="center")
    plt.subplots_adjust(left=0.0, bottom=0.1, right=0.65) """
    plt.show()

def createTable():

    plt.figure()

    ax = plt.gca()
    ax.axis('off')
    table = plt.table(	
    cellText = aggs, colLabels= col_labels, cellLoc= 'center', loc = 'center'
    )
    table.scale(1, 2)
    #plt.show()
    plt.savefig('/home/sergey/Desktop/telegram/total.png')

if __name__ == '__main__':
    print(datetime.datetime.today().date())
    print(datetime.timedelta(days = -7))
    print(datetime.datetime.today().date() + datetime.timedelta(days = -7))