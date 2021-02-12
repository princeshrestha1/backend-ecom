'''
Label Generator for BreadFruit

Author: Manish K. Sharma

###############################
REQUIRED PACKAGE INSTALLATION
###############################
$ brew install ghostscript
$ pip install treepoem
###############################

TO BE USED IN PROJECTS OWNED BY PRIXA TECHNOLOGIES ONLY. 
'''

import treepoem
from PIL import Image, ImageDraw, ImageFont
from django.utils.crypto import get_random_string


#########################
# Edit these values
#########################
# sender_line_1 = "BREADFRUIT ELECTRONICS"
# sender_line_rem = "SATDOBATO - 15\nLALITPUR 44600 \nNP"
# sender_code = sender_line_1 + "\n" + sender_line_rem
# sender_drop_center_code = "SK 001 01-A" # Super Kinetic Labim Mall

def barcode_generator(page_no, receiver_name, receiver_address, contact_number, package_weight, tracking_no, sender_line_1, sender_line_rem, sender_code, sender_drop_center_code,sender_mobile, price):
	
	# pass

	# page_no = "1 of 1"
	# package_weight = "2 LBS"

	# receiver_name = "RAM PRASAD OJHA"
	# receiver_address = "Kaushaltar - 15\nBhaktapur 44809 \nNP"

	

	transport_method = "AYATA AIRWAYS"

	#########################
	# End Edit
	#########################

	margin_x = 20
	margin_y =10
	img = Image.new('RGB', (1200, 1800), color = (255, 255, 255))

	myriad_bold = ImageFont.truetype('myriad_bold.ttf', 50)
	myriad_regular = ImageFont.truetype('myriad_regular.ttf', 50)
	d = ImageDraw.Draw(img)

	d.text((20+margin_x,margin_y+30), sender_line_1 , font=ImageFont.truetype('myriad_bold.ttf', 40), fill=(0, 0, 0))
	w,h1 = d.multiline_textsize(sender_line_rem, font=ImageFont.truetype('myriad_regular.ttf', 40))
	d.text((20+margin_x,margin_y+70), sender_mobile, font=ImageFont.truetype('myriad_regular.ttf', 40), fill=(0, 0, 0))

	d.text((20+margin_x,margin_y+110), sender_line_rem, font=ImageFont.truetype('myriad_regular.ttf', 40), fill=(0, 0, 0))

	d.text((650+margin_x,margin_y+25), package_weight, font=ImageFont.truetype('myriad_bold.ttf', 50), fill=(0, 0, 0))
	
	w, h2 = d.textsize(page_no, font=ImageFont.truetype('myriad_bold.ttf', 40))
	# margin x changes
	w = w + margin_x
	d.text((1180-w,margin_y+25), page_no, font=ImageFont.truetype('myriad_bold.ttf', 40), align="right", fill=(0, 0, 0))

	d.text((700+margin_x,h2+100), price, font=ImageFont.truetype('myriad_bold.ttf', 100), align="right", fill=(0, 0, 0))
	
	h = 130+h1
	d.multiline_text((20+margin_x,h), "SHIP TO:", font=ImageFont.truetype('myriad_regular.ttf', 60), fill=(0, 0, 0), spacing=20)
	w,_ = d.multiline_textsize("SHIP TO:", font=ImageFont.truetype('myriad_regular.ttf', 60))


	d.text((w+80,h), receiver_name, font=ImageFont.truetype('myriad_bold.ttf', 56), fill=(0, 0, 0))
	d.multiline_text((w+80,h+60), contact_number, font=ImageFont.truetype('myriad_regular.ttf', 55), fill=(0, 0, 0), spacing=20)
	_,h2 = d.multiline_textsize(contact_number, font=ImageFont.truetype('myriad_regular.ttf', 55), spacing=20)
	# d.text((w+80,h+120), font=ImageFont.truetype('myriad_regular.ttf', 55), fill=(0, 0, 0))
	d.text((w+80,h+170), receiver_address, font=ImageFont.truetype('myriad_regular.ttf', 55), fill=(0, 0, 0))
	# d.text((w+80,h+175), country, font=ImageFont.truetype('myriad_regular.ttf', 55), fill=(0, 0, 0))

	h=600
	d.line([0,h,1200-margin_x,h],fill=(0, 0, 0),width=2)
	h=h+20

	azteccode = treepoem.generate_barcode(
		barcode_type='azteccode', 
		data=sender_code,
		options={'width':2, 'height':2, 'layers':3, 'format':'full'}
		
	)
	azteccode_img = azteccode.convert('1')
	img.paste(azteccode_img,(20,h))

	h=h+310
	d.line([0,h,1200-margin_x,h],fill=(0, 0, 0),width=15)
	d.line([340,h-330,340,h],fill=(0, 0, 0),width=2)

	sender_drop_center = treepoem.generate_barcode(
		barcode_type='code39ext', 
		data=sender_drop_center_code,
		options={'width':5, 'height':1.0}
		
	)
	d.text((500+margin_x,h-300), sender_drop_center_code, font=ImageFont.truetype('myriad_bold.ttf', 100), fill=(0, 0, 0))
	sender_drop_center_img = sender_drop_center.convert('1')
	img.paste(sender_drop_center_img,(400,h-175))

	h=h+30

	d.text((20+margin_x,h), transport_method, font=ImageFont.truetype('myriad_bold.ttf', 70), fill=(0, 0, 0))
	h=h+80
	d.text((20+margin_x,h), 'TRACKING #: '+tracking_no, font=ImageFont.truetype('myriad_regular.ttf', 50), fill=(0, 0, 0))
	h=h+60
	d.line([0,h,1200-margin_x,h],fill=(0, 0, 0),width=2)
	d.rectangle([1200-170,h-170,1200-margin_x,h], fill=(0,0,0))

	h=h+20
	tracking_code_gen = treepoem.generate_barcode(
		barcode_type='code128', 
		data=tracking_no,
		options={'width':7.5, 'height':1.9}
	)
	tracking_code_img = tracking_code_gen.convert('1')
	img.paste(tracking_code_img,(50,h))

	h=h+300
	d.line([0,h,1200-margin_x,h],fill=(0, 0, 0),width=15)
	h=h+10

	logo = Image.open('logo.jpg')
	newlogo = logo.resize((400, 150))

	# newlogo = newlogo.crop((100,0,100,0))
	# newlogo.show()
	img.paste(newlogo,(400,h))


	h=h+150

	d.line([0,h,1200-margin_x,h],fill=(0, 0, 0),width=2)

	h=h+20
	tracking_code_gen = treepoem.generate_barcode(
		barcode_type='pdf417', 
		data=tracking_no,
		options={'width':6, 'height':1.0, 'columns':2,'eclevel':5}
	)
	tracking_code_img = tracking_code_gen.convert('1')
	img.paste(tracking_code_img,(50,h))

	d.text((1000,h), 'E2', font=ImageFont.truetype('myriad_bold.ttf', 100), fill=(0, 0, 0))

	# img.show()
	# img.save('op.png', dpi=(300,300))

	##############################################
	### OUTPUT. Change here accordingly
	##############################################
	# store multiple pages here (for 1 of 2 etc)
	return img


# to store image to django
def image_save(images, buffer):
	images[0].save(fp=buffer, format="pdf", save_all=True, append_images=images[1:], resolution=300)
