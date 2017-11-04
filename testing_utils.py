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


def array_to_bitstring(array, bits_per_element):
    bitstring = ''
    for value in array:
        bitstring += to_bits(value,bits_per_element,False)
    return bitstring
    
    
def array_to_asciistring(array):
    asciistring = ''
    for value in array:
        asciistring += chr(value)
    return asciistring

