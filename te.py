from PIL import Image, ImageDraw, ImageFont

# values
website = "AboveInsider"
website_url = "https://aboveinsider.com"
da = "45 +"
dr = "60 +"
traffic = "120K +"

# split website name
part1 = "Above"
part2 = "Insider"

# open template
img = Image.open("template.png").convert("RGBA")
draw = ImageDraw.Draw(img)

# fonts
title_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 110)
value_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 43)
url_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 32)

# base position
x = 110
y = 194

# draw first part
draw.text((x, y), part1, fill=(0,0,0), font=title_font)

# measure width of first part
bbox = draw.textbbox((0,0), part1, font=title_font)
width = bbox[2]

# draw second part right after it
draw.text((x + width + 10, y), part2, fill=(29, 154, 247), font=title_font)

# url
draw.text((110,310), website_url, fill=(0,0,0), font=url_font)

# values
draw.text((333,504), da, fill=(0,0,0), font=value_font)
draw.text((333,585), dr, fill=(0,0,0), font=value_font)
draw.text((380,672), traffic, fill=(0,0,0), font=value_font)

# save
img.save("output.png")