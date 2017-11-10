import visa



def configure_current_limit(mx100tp, channel, current_limit):
    command_string = "I" + str(channel) + " " + str(current_limit)
    mx100tp.write(command_string)
    
    
    
def measure_current(mx100tp, channel):
    command_string = "I" + str(channel) +"O?"
    mx100tp.write(command_string)    
    
    
    
def configure_voltage_level(mx100tp, channel, voltage_level):
    command_string = "V" + str(channel) + " " + str(current_limit)
    mx100tp.write(command_string)
    
    
    
def measure_voltage(mx100tp, channel):
    command_string = "V" + str(channel) +"O?"
    mx100tp.write(command_string)

    
    
def enable_output(mx100tp, channel, enable):
    command_string = "OP" + str(channel) + " " + str( int(enable) )
    mx100tp.write(command_string)
    
    
  
    
