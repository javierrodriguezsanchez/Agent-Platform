import PySimpleGUI as sg
from Client.Client_connection import GiveActionsForAgent, ExecuteAction,Search
from Client.DataClient import Load, Save, Delete
from itertools import islice

def Gui_run():
    agents = []
    def SearchGUI(query, agents=agents):
        #this function manage the query made by the user
        for i in Search(query):
            agents.append(i)
            yield Show(i)

    def LoadAgents():
        for i in Load():
            yield Show(i)

    def Show(agent):
        layout=[ 
            [
                sg.Column([[
                sg.Multiline('Descripción Genérica',expand_x=True,size=(75,3),no_scrollbar=False),
                sg.Button('Save',button_color='Green',key='Save\0'+agent),
                sg.Button('Use',button_color='Green',key='Use\0'+agent)
            ]],justification='r',expand_x=True)]]
        
        return [sg.Frame(agent,layout=layout,element_justification='c',expand_x=True)]


    def SelectActionForAgent(agent):
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

    def layout_base():#the standard heading for our app
        return [
            [sg.Text('Agents platform', font=('Helvetica',50))],
            [sg.Input(key='query',size=(35,2)), sg.Button('Search',font=('Arial',14))]
        ]


    sg.theme('DarkAmber')
    sg.set_options(font=('Arial Bold',18))

    layout= layout_base()+ [
        [sg.Text('Saved Agents', font=('Helvetica',30),pad=3)],
        [sg.Column(list(LoadAgents()), scrollable=True, 
                vertical_scroll_only=True, key='scrollable_area',expand_x=True)]
    ]

    window2 = sg.Window('Agents platform', layout, element_justification='c',finalize=True)
    window2.Maximize()


    #EVENTS
    #--------------

    while True:
        event, values = window2.read()
        if event == sg.WIN_CLOSED:#ends the program
            window2.close()
            break
        
        if event[0:3]=='Use':
            agent=event[4:]
            selection=SelectActionForAgent(agent)#gets the categories
            if selection==None:
                continue
            ExecuteAction(agent,selection)
        
        if event[0:4]=='Save':
            agent=event[5:]
            if window2[event].TextColor=='black':
                window2[event].TextColor='red'
                Delete(agent)
                window2[event].update(button_color='green', text='Save')
                continue
            Save(agent)
            window2[event].update(button_color='red', text='Undo')
            window2[event].TextColor='black'

        if event == 'Search':
        #searches a game based on a query
            if values['query'] == '':
                continue
            layout = layout_base()+[[sg.Text('Results for: '+values['query'], font=('Helvetica',30),pad=3)]]
            
            
            #gives the results of the search
            layout=layout+[[sg.Column(list(islice(SearchGUI(values['query']),10)),
                    scrollable=True, vertical_scroll_only=True,
                    key='scrollable_area',expand_x=True, expand_y=True)]]
            
            window2.close()
            window2=sg.Window('VPN', layout, element_justification='c',finalize=True)
            window2.Maximize()
            