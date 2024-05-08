import PySimpleGUI as sg
from Client.Client_conection import GiveAgents, GiveActionsForAgent, ExcecuteAction

def Gui_run():
    agents=GiveAgents()
    def ShowAgents(agents=agents):
        for i in agents:
            yield Show(i)

    def Show(agent):
        layout=[
            [
                sg.Column([[
                sg.Button(agent,key=agent)
            ]],justification='r',expand_x=True)]]
        
        return [sg.Frame(agent,layout=layout,element_justification='c',expand_x=True)]

    def SelectActionForAgent(agent):
    #allows to chose the categories
        actions=GiveActionsForAgent(agent)
        layout=[[sg.Text(f"Actions for {agent}",font=('Helvetica',30))]]+[
            [sg.Button(action, key=action) for action in actions]
            ]
        window2=sg.Window('Select Categories',layout=layout,element_justification='c')

        while True:
            event, values = window2.read()
            
            if event in actions:
                window2.close()
                return event
            
            if event == sg.WIN_CLOSED or event=='Cancel' :
                window2.close()
                return None

    sg.theme('DarkAmber')
    sg.set_options(font=('Arial Bold',18))

    layout=[
        [sg.Text('Agents plataform', font=('Helvetica',50))],
        [sg.Column(list(ShowAgents()), scrollable=True, 
                vertical_scroll_only=True, key='scrollable_area',expand_x=True)]
    ]

    window2 = sg.Window('Agents plataform', layout, element_justification='c',finalize=True)
    window2.Maximize()


    #EVENTS
    #--------------

    while True:
        event, values = window2.read()
        if event == sg.WIN_CLOSED:#ends the program
            window2.close()
            break
        
        if event in agents:
            selection=SelectActionForAgent(event)#gets the categories
            if selection==None:
                continue
            ExcecuteAction(event,selection)

            