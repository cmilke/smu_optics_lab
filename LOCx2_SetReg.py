import visa
import pyvisa
import time
import testing_utils



usb_iss_name = 'COM8'
adc_enum = {'NevisADC':0, 'ADS5272':1, 'ADS5294':2, 'Testmode':3}
ref_clk_delay = 0
delay_array = [17,17,17,17]
write_register_array = [0x0,0x2,0x4,0x6]
read_register_array = [0x1,0x3,0x5,0x7]
init_command = [0x5A,0x2,0x60]



#Be VERY CAREFUL with the ordering of bits in this function!
#The ordering flips directions multiple times.
def locx2_regs_gen(adc_type, ref_clk_delay, delay_array):
    delay_binary = []
    for i in range(4):
        delay_binary.append( testing_utils.to_bits(delay_array[i],8,True) )

    delay_piece0 = delay_binary[0][0:4]
    delay_piece1 = delay_binary[0][4]
    delay_piece2 = delay_binary[1][0:5]
    delay_piece3 = delay_binary[2][0:2]
    delay_piece4 = delay_binary[2][2:5]
    delay_piece5 = delay_binary[3][0:5]

    adc_type_binary = testing_utils.to_bits(adc_type,16,True)[0:2]
    ref_clk_delay_value = [0x0,0x1,0x3][ref_clk_delay]
    ref_clk_delay_value_binary = testing_utils.to_bits(ref_clk_delay_value,8,True)[0:2]

    command_string1 = adc_type_binary + ref_clk_delay_value_binary + delay_piece0
    command_string2 = delay_piece1 + delay_piece2 + delay_piece3
    command_string3 = delay_piece4 + delay_piece5
    print(adc_type_binary+' '+ref_clk_delay_value_binary)
    print(delay_piece0+' '+delay_piece1+' '+delay_piece2)
    print(delay_piece3+' '+delay_piece4+' '+delay_piece5)
    command1 = testing_utils.bitstring_to_integer(command_string1,True)
    command2 = testing_utils.bitstring_to_integer(command_string2,True)
    command3 = testing_utils.bitstring_to_integer(command_string3,True)
    print("COMMANDS: "+format(command1,'02x')+' '+format(command2,'02x')+' '+format(command3,'02x'))

    generated_bytes = [13,command1,command2,command3]
    return generated_bytes



def open_usb_iss(visa_resource_name):
    usb_iss = visa.ResourceManager().open_resource(visa_resource_name)
    usb_iss.open_timeout=10000 #10 seconds
    usb_iss.baud_rate=9600
    usb_iss.data_bits=8
    usb_iss.resource_pyclass = pyvisa.resources.SerialInstrument
    usb_iss.parity = pyvisa.constants.Parity.none
    usb_iss.end_input = pyvisa.constants.SerialTermination.none
    usb_iss.read_termination = None
    usb_iss.write_termination = None
    usb_iss.stop_bits = pyvisa.constants.StopBits.one
    
    return usb_iss
    
    
    
def usb_12c_wr(visa_resource_name, write_mode, read_mode, command):
    usb_iss = open_usb_iss(visa_resource_name)
    if write_mode:
        command_bytes = testing_utils.array_to_rawbytes(command)
        print( "SENDING COMMAND: " + str(command) )
        print( usb_iss.write_raw(command_bytes) )
    time.sleep(.5) #500 milliseconds
    data_read=-1
    if read_mode:
        bytes_to_read = usb_iss.bytes_in_buffer
        print("READING " + str(bytes_to_read) + " BYTES")
        raw_byte, status = usb_iss.visalib.read(usb_iss.session, bytes_to_read )
        data_read = int.from_bytes(raw_byte, byteorder='big')
        print( "READ " + str(data_read) )
    usb_iss.close()
    print()
    return data_read



#TODO: make this more elaborate
def display_test_results(test_passed):
    print('Did test pass? ' + str(test_passed) )



adc_name = 'NevisADC'
adc_type = adc_enum[adc_name]
generated_byte_array = locx2_regs_gen(adc_type, ref_clk_delay, delay_array)

print("Filling Registers\n\n")
usb_12c_wr(usb_iss_name, True, False, init_command)
for register_number in range( len(write_register_array) ):
    write_register = write_register_array[register_number]
    generated_byte = generated_byte_array[register_number]
    write_command = [0x53, write_register, generated_byte]
    usb_12c_wr(usb_iss_name, True, False, write_command)

print("Reading Back Registers")
values_read = []
read_comparison_failed = False
usb_12c_wr(usb_iss_name, True, False, init_command)
for register_number in range( len(read_register_array) ):
    read_register = read_register_array[register_number]
    generated_byte = generated_byte_array[register_number]
    read_command = [0x53, read_register]
    data_read_out = usb_12c_wr(usb_iss_name, True, True, read_command)
    #TODO: print read_command out

    comparison_byte = data_read_out
    values_read.append(comparison_byte)
    read_comparison_failed = comparison_byte != generated_byte
    if read_comparison_failed: break

display_test_results(not read_comparison_failed)
