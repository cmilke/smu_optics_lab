import visa
import time
import testing_utils



visa_resource_name = ''
register_value_file = 'register_values.dat'
fpga_confirmation_response = '33'
correct_status = [1,2,2,0,0]

fpga_uart_communication_protocol_template = [0x4E, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]

strobe_command = [0x4E, 0x1B, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1B, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x4E, 0x1B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

start_command = [0x4E, 0x1C, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1C, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0x4E, 0x1C, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1C, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

read_command = [0x4F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

correct_error_count = [0]*20
scan_time = 10 #seconds



def read_register_values(file_name):
    register_values = []
    register_file = open(file_name)
    for line in register_file:
        register_string, value_string = line.split()
        register = int(register_string,16)
        value = int(value_string,16)
        register_values.append([register,value])
    return register_values



def open_serial_port(visa_resource_name):
    com10_instrument = visa.ResourceManager().open_resource(visa_resource_name,
                                                            open_timeout=10000, #10 seconds
                                                            resource_pyclass=pyvisa.resources.SerialInstrument,
                                                            baud_rate=115200,
                                                            data_bits=8,
                                                            parity=pyvisa.constants.Parity.none,
                                                            stop_bits = pyvisa.constants.StopBits.one)
    return com4_instrument



def paramameter_generator(register_values):
    parameter_list = []

    bit_slice = 256
    for pair in register_values:
        register = pair[0]
        value    = pair[1]
        value_remainder = value % bit_slice
        value_quotient = int(value / bit_slice)

        new_parameter = fpga_uart_communication_protocol_template[:]
        new_parameter[1] = register
        new_parameter[2] = value_remainder
        new_parameter[3] = value_quotient
        new_parameter[9] = register
        new_parameter[10] = value_remainder
        new_parameter[11] = value_quotient

        parameter_list.append(new_parameter)
    return parameter_list



def set_parameters(visa_resource, register_values):
    parameter_list = paramameter_generator(register_values)
    for parameter in parameter_list:
        command = testing_utils.array_to_bitstring(parameter)
        instrument_response = visa.query(command)
        if instrument_response != fpga_confirmation_response:
            print("WrongAck on parameter setting")
            exit(1)
        time.sleep(0.1)



def param_strobe(visa_resource):
    strobe_command_string = testing_utils.array_to_bitstring(strobe_command) 
    response = visa_resource.query(strobe_command_string)
    if response != (fpga_confirmation_response + fpga_confirmation_response):
        print("WrongAck on strobe")
        exit(1)



def locx2_start(visa_resource):
    start_command_string = testing_utils.array_to_bitstring(start_command) 
    response = visa_resource.query(start_command_string)
    if response != (fpga_confirmation_response + fpga_confirmation_response):
        print("WrongAck on start")
        exit(1)



def locx2_read(visa_resource):
    read_command_string = testing_utils.array_to_bitstring(read_command) 
    response = visa_resource.query(read_command_string)
    #TODO: finish this



def param_check(register_values):
    #TODO: finish this
    print("UNDEFINED")




register_values = read_register_values(register_value_file)
visa_resource = open_serial_port(visa_resource_name)
set_parameters(visa_resource, register_values)
param_strobe(visa_resource)
locx2_start(visa_resource)
time.sleep(0.1) #100 milliseconds
locx2_read(visa_resource)
params_written = param_check(register_values)

reading_error = False
elapsed_time = 0.0
scan_start_time = time.time()
while (  elapsed_time < scan_time):
    ack = locx2_read(visa_resource)
    status, error_count, params_read = data_extract(ack)

    status_is_wrong = status != correct_status
    error_count_is_wrong = error_count != correct_error_count
    params_read_are_wrong = params_read != params_written

    if status_is_wrong or error_count_is_wrong or params_read_are_wrong:
        reading_error = True
        break
    eleapsed_time = time.time() - scan_start_time


#display where it failed in detail
serial_close(visa_resource)




