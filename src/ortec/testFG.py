import controller
from controller import DigiBaseController 
import matplotlib.pyplot as plt
if __name__=="__main__":
    dbc=DigiBaseController()

    for det in dbc.getDetList():
        dbc.setHV(det,1000)
        
    dbc.do_startup_checks()
    
    dbc.start_acquisition()
    sample={}
    fine_gain=[0.5,0.8,1.0,1.2]
    f,ax=plt.subplots(ncols=1,nrows=1,figsize=(8,6))
    for fg in fine_gain:
        for det in dbc.getDetList():
            dbc.getDet(det).set_fine_gain(fg)        
        sample=dbc.getSample(duration=10)
        sp=sample[dbc.getDetList()[0]]['spectrum']
        ax.plot(range(len(sp)),sp)

    plt.show()
    


    
