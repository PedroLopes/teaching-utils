#!/usr/bin/env python

from __future__ import print_function
import sys

from reportlab.pdfgen import canvas

point = 1
inch = 72
font_size = 70

width=8.5
height=11

def make_pdf_file(output_filename, lines):
	c = canvas.Canvas(output_filename, pagesize=(width * inch, height * inch))
	c.setStrokeColorRGB(0,0,0)
	c.setFillColorRGB(0,0,0)
	for line in lines:
		c.rotate(90)
		c.setFont("Helvetica", font_size * point) 
		v = 10 * inch
		v -= (font_size * point) + 100
		c.drawString(inch, -v, line)
		c.showPage()
	c.save()
    
if __name__ == "__main__":
	students = [s.strip() for s in sys.stdin.readlines()]
	filename = "students.pdf"
	make_pdf_file(filename, students)
	print ("Wrote", filename)
