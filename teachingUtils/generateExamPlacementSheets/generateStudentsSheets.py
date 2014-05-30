#!/usr/bin/env python

from __future__ import print_function
from sys import argv

from reportlab.pdfgen import canvas

point = 1
inch = 72
font_size = 70

t_students = []
students = []

with open("students.txt") as f:
    t_students = f.readlines()
i=0
for student in t_students:
    students.append(str(t_students[i]).replace('\n',''))
    i+=1	

width=8.5
height=11

def make_pdf_file(output_filename, np):
    title = output_filename
    c = canvas.Canvas(output_filename, pagesize=(width * inch, height * inch))
    c.setStrokeColorRGB(0,0,0)
    c.setFillColorRGB(0,0,0)
    c.setFont("Helvetica", font_size * point) 
    j=0
    for pn in range(1, np + 1):
        v = 10 * inch
	TEXT = students[j]
	j+=1
        for subtline in (TEXT).split( '\n' ):
            c.setFont("Helvetica", font_size * point) 
            c.rotate(90)
            v -= (font_size * point) + 100
            c.drawString( 1 * inch, -v, subtline )
        c.showPage()
    c.save()
    
if __name__ == "__main__":
    nps = [None, len(students)]
    for i, np in enumerate(nps):
        if np:
            filename = "students%d.pdf" % i
            make_pdf_file(filename, np)
            print ("Wrote", filename)
