using UnityEngine;
using System;
using System.Collections;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

public class HandlerScript : MonoBehaviour {

	// Use this for initialization

	public GameObject hero;
	float lpos, rpos;

	Thread receiveThread;
	UdpClient client;
	public int port;

	//info

	public string lastReceivedUDPPacket = "";
	public string allReceivedUDPPackets = "";

	[Space(1f)]
	[Header("Game Stuff")]

	public GameObject boy;
	public GameObject rightarm, leftarm;

	void Start () {
		init();
	}

	public void changey(float y){
//		Debug.Log ("Y : " + y.ToString ());
//		MoveArms (y,y);
	}

	public void MoveArms(float left, float right){
		float l_yrot, r_yrot;

		Debug.Log ("Right : " + right.ToString ());

		l_yrot = ((left) * 70f) + 35f;

		r_yrot = (((right) * -55f) - 35f);

		rightarm.transform.localRotation = (Quaternion.Euler(new Vector3(-0.031f, l_yrot, -179.967f)));

		leftarm.transform.localRotation = (Quaternion.Euler(new Vector3(-2.395f, r_yrot, -181.302f)));

		Debug.Log ("y_rrot : " + l_yrot.ToString ());

	}

	void OnGUI(){
		Rect  rectObj=new Rect (40,10,200,400);

		GUIStyle  style  = new GUIStyle ();

		style .alignment  = TextAnchor.UpperLeft;

		GUI .Box (rectObj,"# UDPReceive\n127.0.0.1 "+port +" #\n"

			//+ "shell> nc -u 127.0.0.1 : "+port +" \n"

			+ "\nLast Packet: \n"+ lastReceivedUDPPacket

			//+ "\n\nAll Messages: \n"+allReceivedUDPPackets

			,style );

	}

	private void init(){
		print ("UPDSend.init()");

		port = 5065;

		print ("Sending to 127.0.0.1 : " + port);

		receiveThread = new Thread (new ThreadStart(ReceiveData));
		receiveThread.IsBackground = true;
		receiveThread.Start ();

	}

	private void ReceiveData(){
		client = new UdpClient (port);
		while (true) {
			try{
				IPEndPoint anyIP = new IPEndPoint(IPAddress.Parse("127.0.0.1"), port);
				byte[] data = client.Receive(ref anyIP);

				string text = Encoding.UTF8.GetString(data);
//				print (">> " + text);
				lastReceivedUDPPacket=text;
				allReceivedUDPPackets=allReceivedUDPPackets+text;

				string[] coors = text.Split (',');
				lpos = float.Parse (coors[0]);
				rpos = float.Parse (coors[1]);
			}catch(Exception e){
				print (e.ToString());
			}
		}
	}

	public string getLatestUDPPacket(){
		allReceivedUDPPackets = "";
		return lastReceivedUDPPacket;
	}

	// Update is called once per frame
	void Update () {
//		hero.transform.position = new Vector3(xPos-6.0f,-3,0);
		Debug.Log ("lpos : " + lpos);
		MoveArms(lpos, rpos);
	}

	void OnApplicationQuit(){
		if (receiveThread != null) {
			receiveThread.Abort();
//			Debug.Log(receiveThread.IsAlive); //must be false
		}
	}
}
