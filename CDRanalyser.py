from flask import Flask, render_template, request
app = Flask(__name__)
import csv
import requests
url = "https://ap1.unwiredlabs.com/v2/process.php"
TOKEN = "YOUR-API-TOKEN"

def Latitude_Longitude(a):
	if(a[0] == "N/A"):
		return("NOTFOUND","NOTFOUND")
	else:
		mcc = a[0]
		mnc = a[1]
		lac = a[2]
		cid = a[3]
		payload = "{\"token\": \""+TOKEN+"\",\"radio\": \"gsm\",\"mcc\":"+mcc+",\"mnc\": "+mnc+",\"cells\": [{\"lac\": "+lac+",\"cid\": "+cid+"}]}"
		response = requests.request("POST", url, data=payload)
		Latitude = float(response.text.split(",")[2].split(":")[1])
		Longitude = float(response.text.split(",")[3].split(":")[1])
		return(Latitude,Longitude)


with open('CDR.csv', newline='') as f:
    reader = csv.reader(f)
    l = list(reader)
l = l[2:]

with open('Coordinates.csv', newline='') as f:
    reader = csv.reader(f)
    Coordinates_List = list(reader)

IMEI = l[0][9]
IMSI = l[0][10]

d = []
for i in range(len(l)):
    d.append(l[i][3])
dd = list(set(d))
dd.sort(reverse=True)
Dates = []
for i in range(len(dd)):
    Dates.append([dd[i], d.count(dd[i])])
Dates[0].append(0)
Dates[0].append(Dates[0][1]-1)

for i in range(1, len(Dates)):
    Dates[i].append(Dates[i-1][-1]+1)
    Dates[i].append(Dates[i][1] + Dates[i-1][-1])

Called_Party = []
for i in range(len(l)):
    Called_Party.append(l[i][2])

Calling_Time = []
for i in range(len(l)):
    Calling_Time.append(l[i][4])

Duration = []
for i in range(len(l)):
    Duration.append(int(l[i][5]))

Tower_ID = []
for i in range(len(l)):
    Tower_ID.append([ (l[i][6][:3]+"-"+l[i][6][3:]).split("-"), (l[i][7][:3]+"-"+l[i][7][3:]).split("-") ])
for i in range(len(Tower_ID)):
    if(Tower_ID[i][1][0] == "N/A"):
        Tower_ID[i][1] = "NOT FOUND"

def Longest_Call(date):
    for i in range(len(Dates)):
        if Dates[i][0] == date:
            a = Duration[Dates[i][2]:Dates[i][3]+1]
    lon = Duration.index(max(a))
    return(Called_Party[lon], Calling_Time[lon], Duration[lon], Coordinates_List[lon][0], Coordinates_List[lon][1])


def First_Call(date):
    for i in range(len(Dates)):
        if Dates[i][0] == date:
            pos = Dates[i][3]
    return(Called_Party[pos], Calling_Time[pos], Duration[pos], Coordinates_List[pos][0], Coordinates_List[pos][1])


def Last_Call(date):
    for i in range(len(Dates)):
        if Dates[i][0] == date:
            pos = Dates[i][2]
    return(Called_Party[pos], Calling_Time[pos], Duration[pos], Coordinates_List[pos][0], Coordinates_List[pos][1])


def Most_Frequently_Dialed(date):
    for i in range(len(Dates)):
        if Dates[i][0] == date:
            start,end = Dates[i][2], Dates[i][3]
    List = Called_Party[start:(end+1)]
    return( max(set(List), key = List.count), List.count(max(set(List), key = List.count)) )

def Longest_Call_General(a):
    lon = a.index(max(a))
    Number = Called_Party[lon]
    Originating_Coordinates = Coordinates_List[lon][0]
    Ending_Coordinates = Coordinates_List[lon][1]
    Date = l[lon][3]
    Time = max(a)
    return(Number, Date, Time, Originating_Coordinates, Ending_Coordinates)

Most_Frequently_Dialed_General = max(set(Called_Party), key = Called_Party.count), Called_Party.count(max(set(Called_Party), key = Called_Party.count))
Longest_Call_Data = Longest_Call_General(Duration)


General_Info = {
		"IMSI": IMSI,
		"IMEI": IMEI,
		"MostFrequentlyDialed": Most_Frequently_Dialed_General,
		"LongestCall": Longest_Call_Data[0],
		"LongestCallDate": Longest_Call_Data[1],
		"LongestCallTime": Longest_Call_Data[2],
		"LongestCallOriginatingLocation": Longest_Call_Data[3],
		"LongestCallEndingLocation": Longest_Call_Data[4],
		"LongOrigLat": Longest_Call_Data[3].split(",")[0][1:],
		"LongOrigLng": Longest_Call_Data[3].split(",")[1][:-1],
		"LongEndLat": Longest_Call_Data[4].split(",")[0][1:],
		"LongEndLng": Longest_Call_Data[3].split(",")[1][:-1]
}


def Calls_Data(date):
    for i in range(len(Dates)):
        if Dates[i][0] == date:
            start,end = Dates[i][2], Dates[i][3]
    
    DATEDATA = []
    for i in range(start, end+1):
        DATEDATA.append([Called_Party[i], Calling_Time[i], Duration[i], Tower_ID[i], Coordinates_List[i][0], Coordinates_List[i][1]])
    return(DATEDATA)


def Create_data(date):
    DATA = {
        	"longest_call": Longest_Call(date),
        	"first_call": First_Call(date),
        	"last_call": Last_Call(date),
        	"most_frequently_dialed": Most_Frequently_Dialed(date),
        	"date": date,
        	"Length": len(Tower_ID)
    }
    return(DATA)


@app.route("/home")
@app.route("/")
def home():
	return(render_template('home.html', general_info=General_Info, dates=Dates))


@app.route("/Date", methods=['GET'])
def Display():
	Selected_Date = request.args.get('SelectedDate')
	DATA = Create_data(Selected_Date)
	Call_DATA = Calls_Data(Selected_Date)
	return(render_template('Date.html', post=DATA, callpost=Call_DATA, postlen=len(Call_DATA)))
