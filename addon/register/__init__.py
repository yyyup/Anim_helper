 





def register_addon():

    #menus
    from ..ui import register_panels
    register_panels()

    #operators
    from ..operators import register_operators
    register_operators()

 


def unregister_addon():
    
    #menus
    from ..ui import unregister_panels
    unregister_panels()



    #operators
    from ..operators import unregister_operators
    unregister_operators()

    