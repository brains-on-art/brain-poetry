import hypermedia.net.*;
import java.util.*;
import java.io.*;
//import processing.serial.*;

//for running threads
String[] daemon_args;
ExecThread daemon_thr;

//PrintThread printer;

// UDP-socket object
UDP udp;
int sendport = 4332;
int recvport = 4333;

int state;

RingBuffer[] channels;
//RingBuffer data;

String poem;
//String printerPoem;
int poemAnimCount;
int creationDelayStart;
int reflectionDelayStart;
boolean ascending; //for color animation

String[] args;

//----------------------------------------------------------
String waitingForUser_f = "Laita EPOC päähän ja paina ENTER!";
String waitingForUser = "Place EPOC on head and press ENTER!";
String[] waitingForUserArr = {waitingForUser_f, waitingForUser};

String howToWear_f = "Liu'ta laite päähäsi päälaelta.\nÄLÄ VÄÄNNÄ VÄKISIN! :(";
String howToWear = "Slide the device from above.\nDON'T WRING FORCIBLY! :(";
String[] howToWearArr = {howToWear_f, howToWear};

String namePrompt_f = "Kirjoita nimimerkkisi ja paina ENTER.";
String namePrompt = "Write your name and press ENTER.";
String[] namePromptArr = {namePrompt_f, namePrompt};

String[] standByArray1_f = {"Kerätään dataa.", "Suodatetaan dataa.",
                    "Lasketaan ajatusten tehospektriä.",
                    "Paikannetaan alfa-piikkiä.", "Etsitään aivoja."};
String[] standByArray1 = {"Collecting data.", "Filtering data.",
                    "Calculating power spectrum.",
                    "Locating alpha spike.", "Searching for brains."};
String[][] standByArray1Arr = {standByArray1_f, standByArray1};

String[] standByArray2_f = {"Meditoidaan.",
                    "Odotetaan inspiraatiota.", "Paneudutaan aihepiiriin.",
                    "Ahmitaan ajatuksia.", "Sisäistetään metaforia.",
                    "Inhimillistetään maailmankuvaa.", "Yritetään samaistua.",
                    "Täytetään empatiapuskuria."};
String[] standByArray2 = {"Meditating.", "Waiting for inspiration.", "Delving into your thoughts.",
                    "Filling empathy buffer.", "Humanizing wordview.", "Trying to relate.", "Processing thoughts.",
                    "Internalizing imagery."};
String[][] standByArray2Arr = {standByArray2_f, standByArray2};

String standBy3_f = "Odota hetki, luodaan runoa.";
String standBy3 = "Creating poem, please wait.";
String[] standBy3Arr = {standBy3_f, standBy3};

String startNewPrompt_f = "Uusi runo\nSUOMEKSI";
String startNewPrompt = "New poem in\nENGLISH";
String[] startNewPromptArr = {startNewPrompt_f, startNewPrompt};

String[] anon = {"Anonyymi", "Anonymous"};

int standByIndex1; //for randomisation of messages
int standByIndex2;

int lang = 1; //0 for FIN, 1 for ENG. used as index for static arrays

//for having a different delay each run
int standBy1Delay = 2;
int standBy2Delay = 2;
int standBy3Delay = 2;
int standByDelayTotal = standBy1Delay + standBy2Delay + standBy3Delay;

int reflectionDelay = 10;


String userName ="";
PFont font;
color bgcolor = 0;
int rightHorMargin;
int leftHorMargin;

//modifier key flag for exiting
boolean modDown = false;

PImage instructionImage;

void setup() {
  // load instruction image
  imageMode(CENTER);
  instructionImage = loadImage("headset1.png");
  instructionImage.resize(displayWidth/2,0);
  noCursor();
  //start backend
  //daemon_args = new String[]{"python", "../Runokoneistoa/Apparatus/runo_backend_daemon.py", "> log.txt"};
  //daemon_args = new String[]{"python", "../runo_backend_daemon.py"};
  //daemon_thr = new ExecThread(daemon_args);
  //daemon_thr.start();
  
  //layout stuff
  size(displayWidth,displayHeight);
  background(bgcolor);
  leftHorMargin = 0;
  rightHorMargin = 0;
  
  //init UPD connection: it's of type datagram
  udp = new UDP(this, recvport);
  udp.listen(true);
  
  //prepare dataArray
  channels = new RingBuffer[5];
  for (int i=0; i<channels.length; i++) {
    channels[i] = new RingBuffer(width - leftHorMargin - rightHorMargin);
  }
  //data = new RingBuffer(width - leftHorMargin - rightHorMargin);
  
  //flag for system state
  state = 0;
  
  //prepare for drawing text
  font = createFont("Serif.plain", 50, true);
  textFont(font, 20);
  //textSize(20);
  //println(g.textLeading);
  smooth();
  poemAnimCount = 0;
  creationDelayStart = 0;
  standByIndex1 = 0;
  standByIndex2 = 0;
  ascending = true;
  
  //throttle framerate so text cursor blinks at a reasonable rate
  frameRate(24);
  
}

//MAINLOOP
void draw() {
  //line and bg color
  stroke(255);
  drawData(255, 50);
  
  //text color
  fill(255);
  textFont(font, 20);


  //check state and draw things accordingly
  if (state == 0) { //idle and waiting for a new user
    //drawData(0);
    image(instructionImage,displayWidth/2,  2*(displayHeight/4));
    fill(255);
    textAlign(CENTER);
    text(waitingForUserArr[lang], width/2, height/4);
    text(howToWearArr[lang],width/2,3*(height/4));
  }
  else if (state == 1) { //we have a user! gather data and name while showing data
    //drawData(0);
    
    textAlign(CENTER);
    text(namePromptArr[lang], width/2, height/2-30);
    //textAlign(RIGHT);    
    text(userName+(frameCount/10 % 2 == 0 ? "|" : " "), width/2, (height/2)+30);
  }
  else if (state == 2) { //user gave their name. continue showing data and wait for poem
    //drawData(0);
    //text("Odota hetki, luodaan runoa."+(frameCount/10 % 2 == 0 ? (frameCount/15 % 2 == 0 ? "." : "..") : " "), (width/4)*3, height/2);
    
    if (creationDelayStart==0) {
      //text("Still zero", width/2, (height/2)-200);
      //text("StandByDelayTotal*24 == " + str(standByDelayTotal*24), width/2, height/2);
      //text("frameCount-creationDelayStart == " + str(frameCount-creationDelayStart), width/2, height/2+100);
      text(standByArray1Arr[lang][standByIndex1], width/2, height/2);
    }
    else if (frameCount-creationDelayStart < standByDelayTotal*24) {
        //poem hasn't arrived yet ... or we haven't delayed long enough
      
      if ((creationDelayStart==0) || (frameCount-creationDelayStart < standBy1Delay*24)) {
      text(standByArray1Arr[lang][standByIndex1], width/2, height/2);
      
      //text("StandByDelayTotal*24 == " + str(standByDelayTotal*24), width/2, height/2);
      //text("frameCount-creationDelayStart == " + str(frameCount-creationDelayStart), width/2, height/2+100);
      }
      
      //WHAT THE FUCK IS GOING ON HERE MAN
      else if ((frameCount-creationDelayStart >= standBy1Delay*24) && (frameCount-creationDelayStart < (standBy1Delay+standBy2Delay)*24)) {
      text(standByArray2Arr[lang][standByIndex2], width/2, height/2);
      }
      else if ((frameCount-creationDelayStart >= (standBy1Delay+standBy2Delay)*24) && (frameCount-creationDelayStart < standByDelayTotal*24)) {
      text(standBy3Arr[lang], width/2, height/2);
      }
    }
    else {
      state = 3;
    }
    
  }
  else if (state == 3 || state == 4) { //we got poem from python. show it as animation
    textAlign(LEFT);

    //we'll do this every iteration because it isn't really that expensive
    float h = heightOfString(poem);
    float poemUpperY = (height - h)/2;
    float poemUpperX = (width - textWidth(poem))/2;

    if (poemAnimCount < poem.length()) {
      poemAnimCount++;
      text(poem.substring(0, poemAnimCount), poemUpperX, poemUpperY);
    }
    else {
      //println(poem);
      //println(userName);
      text(poem, poemUpperX, poemUpperY);

      state = 5;
      udp.send("print", "localhost", sendport);
      //reflectionDelayStart = frameCount;
    }
  }
  else if (state == 5) {
    float h = heightOfString(poem);
    float poemUpperY = (height - h)/2;
    float poemUpperX = (width - textWidth(poem))/2;
    
    
    //textFont(font, 20);
    //fill(100);
    textAlign(LEFT);
    text(poem, poemUpperX, poemUpperY);
    
    textAlign(CENTER);
    //textSize(50);
    //textFont(font, 50);
    fill(255*abs(2*((frameCount/30.0)-floor((frameCount/30.0)+0.5))));
    //text("ENTER", width/2, (height-poemUpperY+heightOfString(poem))+50);
    text("ENTER", width/2, height-50);

    
    /*
    if (frameCount-reflectionDelayStart < reflectionDelay*24) {
      //we'll show only the poem for some time
      //fill(255);
      text(poem, poemUpperX, poemUpperY);
      
    } */
    
    }
    else if (state == 6) {
      float h = heightOfString(poem);
      float poemUpperY = (height - h)/2;
      float poemUpperX = (width - textWidth(poem))/2;
      textAlign(LEFT);
      fill(255, 40);
      text(poem, poemUpperX, poemUpperY);

      textAlign(CENTER);
      stroke(255*abs(2*((frameCount/30.0)-floor((frameCount/30.0)+0.5))));
      
      rectMode(CENTER);
      noFill();
      int[] rectXCenter = {(width/2)-200, (width/2)+200};
      rect(rectXCenter[lang], (height/2)+15, 340, 180);
      fill(255);
      textSize(40);
      text(startNewPromptArr[0], (width/2)-200, height/2);
      text(startNewPromptArr[1], (width/2)+200, height/2);
    //}
  }
}

//plotter for data
void drawData(float strokeColor, float alpha) {
  background(bgcolor);
  //line(width/2, 0, width/2, height);
  stroke(strokeColor, alpha); 
  float hmod = height/(channels.length*2); //hmod controls the scale and position of the channels (assume -1<data<1)
  float drawH = hmod;
  for (int ch=0; ch<channels.length; ch++) {
    for (int i=0; i<channels[ch].size()-1; i++) {
      line(leftHorMargin+i, drawH+(channels[ch].get(i)*hmod), leftHorMargin+i+1, drawH+(channels[ch].get(i+1)*hmod));
    }
    drawH += 2*hmod;
  }
}

float heightOfString(String str) {
  int matches = 0;
  for (int i=0; i<str.length(); i++) {
    if (str.charAt(i) == '\n') {
      matches++;
    }
  }
  return ((textAscent()+textDescent()) * 1.275f * matches);
}

void keyPressed() {
  //println(keyCode);
  if(keyCode==ESC || key == ESC){
    key = 0;
    keyCode = 0;  
  }
  if (keyCode==524) {
    modDown = true;
  }
  if (keyCode==127) {
    if (modDown == true) {
      exit();
    }
  }
}

void keyTyped() {
  if(keyCode==ESC || key == ESC){ 
    key = 0; 
    keyCode = 0;   
  }
}

void keyReleased() {
  if (keyCode==524) {
    modDown = false;
  }

  if (keyCode==127) {
    if (modDown == true) {
      exit();
    }
  }

  if(keyCode==ESC || key == ESC){ 
    key = 0; 
    keyCode = 0;   
  }

  if (state == 0) {
    if (key == ENTER) {
      udp.send("start "+str(lang), "localhost", sendport);
      state = 1;
    }
  }
  else if (state == 1) {
    if (key != CODED) {
      switch(key) {
        case BACKSPACE:
          userName = userName.substring(0,max(0,userName.length()-1));
          break;
        case ENTER:
        case RETURN:
          //user is done. send name to db and proceed to next state
          state = 2;
          if (userName.equals("")) {
            userName = anon[lang];
          }
          userName = "["+userName+"]";
          println("Sending name "+userName);
          udp.send("n"+userName, "localhost", sendport);
          break;
        case ESC:
        case DELETE:
          break;
        default:
          if (!(userName.length()>30)) {
            userName += key;
          }
        }
     }
  }
  else if ((state == 2) || (state == 3) || (state == 4)) {
    //user shan't do anything here, we're in the middle of showing the poem
  }
  
  else if(state == 5) {
    if (key == ENTER) {
      state = 6;
    }
  }
  
  //when we're done showing the poem (and letting the viewer reflect on it)...
  else if (state == 6) {

    // DO LANGUAGE SELECTION HERE. MAYBE ALPHA OUT THE POEM AND PUT THIS ON TOP
    if (keyCode == LEFT || keyCode == RIGHT) {
      println(lang);
      lang = (lang == 0) ? 1 : 0;
      println(lang);
    }
    
    //  ...give user chance to end session or new user to start a new one
    //  i.e. to switch state to 0 with button press or smthng
    if (key == ENTER) {
      udp.send("done", "localhost", sendport);
      userName = "";
      poemAnimCount = 0;
      state = 0;
      poem = null;
      //printerPoem = null;
      creationDelayStart = 0;
      standBy1Delay = 2;
      standBy2Delay = 2;
      standBy3Delay = 2;
      standByDelayTotal = standBy1Delay + standBy2Delay + standBy3Delay;
      println(standBy1Delay);
      println(standBy2Delay);
      println(standBy3Delay);
    }
  }
}

/**
 * To perform any action on datagram reception, you need to implement this 
 * handler in your code. This method will be automatically called by the UDP 
 * object each time he receive a nonnull message.
 */
void receive( byte[] packet, String ip, int port ) {  // <-- extended handler
  // get the "real" message =
 






   // forget the ";\n" at the end <-- !!! only for a communication with Pd !!!
  
  // data = subset(data, 0, data.length-2);
  String message = new String( packet );
  //println( "receive: \""+message+"\" from "+ip+" on port "+port );
  
  //println(message);

  //if we're in data-gathering states, collect all data into one array
  if (message.substring(0, 1).equals("d")) {
    //data.add(Float.parseFloat(message.substring(1)));
    String[] vals = message.substring(1).split(",");
    for (int i=0; i< vals.length; i++) {
      channels[i].add(Float.parseFloat(vals[i]));
    }
  }
  //got a poem!
  else if (message.substring(0, 1).equals("p")) {
    //...so switch to poempresentation state
    poem = message.substring(1);
    //printerPoem = linebreaker(poem,32);
    //printerPoem = poem;
    poem = poem+"\n\n"+userName;
    println(userName);
    println(poem);
    //printerPoem = printerPoem.replace("\n\n","\n");
    creationDelayStart = frameCount;
    standByIndex1 = (int)random(standByArray1Arr[lang].length);
    standByIndex2 = (int)random(standByArray2Arr[lang].length);
    //state = 3;
  }
}

//IT'S A HACK! ONLY FOR FLOAT VALUES
public class RingBuffer {
  ArrayList<Float> l;
  int oldest;
  int capacity;

  public RingBuffer(int maxcapacity) {
    l = new ArrayList<Float>();
    capacity = maxcapacity;
    for (int i=0; i<capacity; i++) {
      l.add((float)0);
    }
    oldest = 0;
  }

  private int convertIndex(int i) {
    int beforeEnd = capacity-1 - oldest;
    
    if (i<0 || i>capacity-1) {
      throw new IndexOutOfBoundsException();
    }
    
    else if (i == 0) {
      return oldest;
    }
    return (i <= beforeEnd) ? oldest+i : i-beforeEnd-1;
  }

  public float get(int i) {
    int newi = convertIndex(i);
    //println("Converted "+i+" to newindex " +newi);
    return (float) l.get(newi);
  }

  public void add(float v) {
    //println("Adding, oldest == " + oldest);
    l.set(oldest, v);
    if (oldest == capacity-1) {
      oldest = 0;
      return;
    }
    oldest++;
  }

  public int size() {
    return capacity;
  }
}

public class ExecThread extends Thread {
  String[] args;
  Process p;
  Runtime r;
  ExecThread(String[] args) {
    this.args = args;
    r = Runtime.getRuntime();
  }
  
  void run() {
    try {
      p = r.exec(args);
    } catch (Exception e) {
      println(e);
    }
  } 
}
