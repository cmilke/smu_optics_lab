def to_bits(value, number_of_bits, reverse):
    format_string = '0' + str(number_of_bits) + 'b'
    bit_string = format(value,format_string)
    if reverse:
        return bit_string[::-1]
    else:
        return bit_string



def to_integer(bit_string, is_reversed):
    if is_reversed:
        return int(bit_string[::-1],2)
    else:
        return int(bit_string,2)


def array_to_bitstring(array, bits_per_element, reverse):
    bitstring = ''
    for value in array:
        bitstring += to_bits(value,bits_per_element,reverse)
    return bitstring
    
    
    
def rawbytes_to_array(rawbytes):
    array = []
    for value in rawbytes:
        array.append(value)
    return array
    
   
   
def array_to_rawbytes(array):
    rawbytes = bytes()
    for value in array:
        rawbytes += bytes.fromhex( format(value,'02x') )
    return rawbytes

