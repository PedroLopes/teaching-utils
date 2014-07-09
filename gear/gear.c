//
// Copyrights :  you can do anything you want with this program
//               as long as any work derived from it contains the following message :
//                "Derived from gear.c  by Dries Pruimboom" .
//
//  So, what do you need :
//    Open office, since it generates an .odg open office drawing file
//    zip, since is is used to zip the contents of the .odg file together again.
//
//  How to get it working?
//   well make sure that you execute this program from the directory that the 'odg'
//   directory is in, this odg directory contains all stuff that open office need in a
//   document, and the program needs to find it. 
//
//   then run the 'gear' program like this  "gear 12"  >> creates a .odg with a 12 tooth gear
//
//  Changing the tooth shape, there is this table in the source called 'CoordList' this defines
//  a single tooth, then there is the variable 'ToothWidth' that needs to be set accordingly.
//   
//   well, you will manage !
//
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define PI 3.141592654

//
// For ease of use use a global file var . . . 
//
FILE *gf=NULL;

//
// Scale Setting :
//
float Scale=1.0;

//
// Simple struct for a coordinate
//
typedef struct Coord {
                       float x;
                       float y;
                     } Coord;
                     
                     
//
// this coordlist describes one tooth in cm, be aware that the toothwidth
// must be set accordingly. 
//
float ToothWidth=1.4;                 //  << must be set to the with of a tooth
Coord CoordList[]= { {0   ,  0 },
                     {0.2 , 0.5},
                     {0.7 , 0.5},
                     {0.9 , 0  },
                     {1.4 , 0  },
                     {-1000,-1000}    // end marker (a big negative number. . or is that small well wathever. . .).. 
                   };
                   
    
//
// Get the radius of the circle according to the width of the tooth and the nr of tooth .
//               
float GetRadius(float width,int nroftooth)
{
   //
   // If there are 5 tooth of 2 cm the circle must have an outside of 5*2 = 10 cm
   // this means the radius is 10/(2*pi)
   //
   return ((width*(float)nroftooth)/(PI*2));
}


//
// convert a radius and an angle to a coord (basic math). . 
//
void RadiusAndAngleToCoord(float radius,float angle,Coord *c)
{
   c->x = cos(angle)*radius;
   c->y = sin(angle)*radius;
} 


//
// Make an open office compatible line . .
//
MakeLine(float x1,float y1,float x2,float y2)
{
      
      x1 *= Scale;
      y1 *= Scale;
      x2 *= Scale;
      y2 *= Scale;
      
      //
      // output in a format that open office can use
      //
      fprintf(gf,"<draw:line draw:style-name=\"gr1\" draw:text-style-name=\"P1\" draw:layer=\"layout\" svg:x1=\"%fcm\" svg:y1=\"%fcm\" svg:x2=\"%fcm\" svg:y2=\"%fcm\">\n",
              x1,
              y1,
              x2,
              y2);
      fprintf(gf,"<text:p/>\n");
      fprintf(gf,"</draw:line>\n");
}

//
// Make the code for a single tooth. . 
//
int DrawTooth(int nroftooth,int toothnr,float toothwidth)
{
   float radius;
   float mid;
   Coord pos_1;
   Coord pos_2;
   float angle_1;
   float angle_2;
   float radius_1;
   float radius_2;
   float stretch;
   int i;
  
   //
   // Get radius of the gear
   //       
   radius = GetRadius(toothwidth,nroftooth);   
      
      
   //
   // We estimate a good middle point for the gear, if the tooth height is 
   // bigger than the 1 cm we add here, problems might arise. . 
   //
   mid = radius+2;
   
   //
   // Calculate the starting stretch :
   //
   stretch = (float)toothnr*toothwidth;


   //
   // Draw a centre line .. 
   //
   MakeLine(mid-0.5,mid-0.5,mid+0.5,mid+0.5);
   MakeLine(mid+0.5,mid-0.5,mid-0.5,mid+0.5);
   
   //
   // Now get and calculate all the points. on a line from the centre
   //     
   i=1;                      
   while (CoordList[i].x > -999)
   {
      //
      // Xposition determines the angle on the circle by means of the 'stretch'
      //
      angle_1 = (stretch/radius)+(CoordList[i-1].x/radius);
      radius_1  = radius+CoordList[i-1].y;
      
      angle_2 = (stretch/radius)+(CoordList[i].x/radius);
      radius_2  = radius+CoordList[i].y;
      
      //
      // Get this stuff back to coords
      //
      RadiusAndAngleToCoord(radius_1,angle_1,&pos_1);
      RadiusAndAngleToCoord(radius_2,angle_2,&pos_2);
      
      //
      // center. . 
      //
      pos_1.x += mid;
      pos_1.y += mid;
      pos_2.x += mid;
      pos_2.y += mid;

      //
      // Output the line. . .
      //
      MakeLine(pos_1.x,pos_1.y,pos_2.x,pos_2.y);
      
      i++;
   }
   printf("\n");
}                   
 
//
// Draw a complete gear with a certain nr of tooth . . 
//
void DrawGear(int nroftooth)
{
   int x;
   
   for (x=0;x<nroftooth;x++)
   {
      DrawTooth(nroftooth,x,ToothWidth);
   }
} 

//
// open the 'odg/content.xml' file and write the stuff that open office needs
// be aware that one of these lines is really really long. . .
//
void OpenODGContent(void)
{
   
   gf = fopen("odg/content.xml","w");
   if (gf==NULL)
   {
      printf("Could not open outputfile, make sure you are in the 'gear' directory\n");
   }
   
   fprintf(gf,"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
   fprintf(gf,"<office:document-content xmlns:office=\"urn:oasis:names:tc:opendocument:xmlns:office:1.0\" xmlns:style=\"urn:oasis:names:tc:opendocument:xmlns:style:1.0\" xmlns:text=\"urn:oasis:names:tc:opendocument:xmlns:text:1.0\" xmlns:table=\"urn:oasis:names:tc:opendocument:xmlns:table:1.0\" xmlns:draw=\"urn:oasis:names:tc:opendocument:xmlns:drawing:1.0\" xmlns:fo=\"urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" xmlns:dc=\"http://purl.org/dc/elements/1.1/\" xmlns:meta=\"urn:oasis:names:tc:opendocument:xmlns:meta:1.0\" xmlns:number=\"urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0\" xmlns:presentation=\"urn:oasis:names:tc:opendocument:xmlns:presentation:1.0\" xmlns:svg=\"urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0\" xmlns:chart=\"urn:oasis:names:tc:opendocument:xmlns:chart:1.0\" xmlns:dr3d=\"urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0\" xmlns:math=\"http://www.w3.org/1998/Math/MathML\" xmlns:form=\"urn:oasis:names:tc:opendocument:xmlns:form:1.0\" xmlns:script=\"urn:oasis:names:tc:opendocument:xmlns:script:1.0\" xmlns:ooo=\"http://openoffice.org/2004/office\" xmlns:ooow=\"http://openoffice.org/2004/writer\" xmlns:oooc=\"http://openoffice.org/2004/calc\" xmlns:dom=\"http://www.w3.org/2001/xml-events\" xmlns:xforms=\"http://www.w3.org/2002/xforms\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:smil=\"urn:oasis:names:tc:opendocument:xmlns:smil-compatible:1.0\" xmlns:anim=\"urn:oasis:names:tc:opendocument:xmlns:animation:1.0\" office:version=\"1.0\">\n");
   fprintf(gf,"<office:scripts/>\n");
   fprintf(gf,"<office:automatic-styles>\n");
   fprintf(gf,"<style:style style:name=\"dp1\" style:family=\"drawing-page\"/>\n");
   fprintf(gf,"<style:style style:name=\"gr1\" style:family=\"graphic\" style:parent-style-name=\"standard\">\n ");
   fprintf(gf,"<style:graphic-properties draw:textarea-horizontal-align=\"center\" draw:textarea-vertical-align=\"middle\"/>\n");
   fprintf(gf,"</style:style>\n");
   fprintf(gf,"<style:style style:name=\"P1\" style:family=\"paragraph\">\n");
   fprintf(gf,"<style:paragraph-properties fo:text-align=\"center\"/>\n");
   fprintf(gf,"</style:style>\n");
   fprintf(gf,"</office:automatic-styles>\n");
   fprintf(gf,"<office:body>\n");
   fprintf(gf,"<office:drawing>\n");
   fprintf(gf,"<draw:page draw:name=\"page1\" draw:style-name=\"dp1\" draw:master-page-name=\"Default\">\n");
   fprintf(gf,"<office:forms form:automatic-focus=\"false\" form:apply-design-mode=\"false\"/>\n");

 
   
}
        

//
// Write the ending of the content.xml file and close the odg/content.xml file
//
void CloseODGContent(void)
{
   fprintf(gf,"</draw:page>\n");
   fprintf(gf,"</office:drawing>\n");
   fprintf(gf,"</office:body>\n");
   fprintf(gf,"</office:document-content>\n");

   fclose(gf);
}
           
//
// Main program, handle command line args and make the gear. . 
//
int main(int argc,char **argv)
{
   int x=1;
   int NrOfTooth=8;
   
   if (argc<1)
   {
      printf("Usage : gear [-scale scale] NrOfTeeth\n");
      printf("          scale is a multiply factor for the size of the gears, 2=bigger 0.1 is smaller. .\n\n");
      
      printf("       this program NEEDS the odg directory in the directory that it is executed.\n");
      printf("       the odg directory contains an unzipped open office .odg file, the gear\n");
      printf("       program creates a new 'content.xml' file and zips it up to a new gear.odg file\n");
      printf("        Halleluja for open formats, Halleluja for readable files. . .\n");
      printf("\n\nPlease read the readme that came with this program. .      grtz Dries Pruimboom 2006\n");
      exit(0);
   }

   while (x<argc)
   {
       if (strcasecmp(argv[x],"-SCALE")==0)
       {
          x++;
          Scale = (float) atof(argv[x]);
	  printf("Scale set to : %f\n",Scale);
       }
       else
       {
         NrOfTooth = atoi(argv[x]);
       }
       x++;
   }

   if (NrOfTooth<2)
   {
      printf("Nr of gears needs to be at least 2 !\n");
      exit(0);
   }

   //
   // Well, this is kind a clear i think . .
   //
   OpenODGContent();
   DrawGear(NrOfTooth);
   CloseODGContent();
   
   //
   // These calls zip the new content file together with the rest of the files to
   // form a valid open office file.
   // then copy it from .zip to a .odg file and done, you can now load it with open office !
   //
   // afterwards, you can use open office to open the file called gear.odg ! don't you love those open 
   //  (and readable) formats !!
   //
   system("cd odg;zip -r gear.zip *");
   system("mv odg/gear.zip gear.odg");
   
}                 


