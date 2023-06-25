
def cf1(value):
    data = str(value).replace(',', '.')
    try:
        number = float(data)
    except ValueError:
        return 'FV'
    if 0 <= number <= 10:
        if number == 0: return '0'
        if number <= 3.5: return '3.5'
        if number <= 4.9: return '4.5'
        if number <= 10: return '7.5'
    else:
        return 'FV'

def normalizador(value):
    return {
        'FV': 'FV',
        '0': 'SC',
        '3.5': 'AC',
        '4.5': 'EC',
        '7.5': 'C'
    }.get(cf1(value), 'FV')

