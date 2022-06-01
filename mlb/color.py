import math

def parse_hex_color(string):
    if string.startswith("#"):
        string = string[1:]
    r = int(string[0:2], 16) # red color value
    g = int(string[2:4], 16) # green color value
    b = int(string[4:6], 16) # blue color value
    return r, g, b, 255
# Calculate distance btw two color
def color_similarity(base_col_val,oth_col_val):
    base = parse_hex_color(base_col_val)
    oth = parse_hex_color(oth_col_val)
    lightest = base_col_val
    if sum(base) < sum(oth):
        lightest = oth_col_val
    return (math.sqrt(sum((base[i]-oth[i])**2 for i in range(3))), lightest)