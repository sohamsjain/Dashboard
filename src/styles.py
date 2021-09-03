from collections import defaultdict
from src.util import XoneStatus


m2 = "m-2"
m3 = "m-3"
my2 = "my-2"
p3 = "p-3"


labelstyle = {
    "font-size": "16px"
}
textstyle = {
    "font-size": "12px"
}


StyleEntryDefault = {
    "background-color": "",
    "color": "black",
    "border": "",
    "border-radius": "10px",
    "font-size": "20px",
    "text-align": "center"
}
StyleEntry = defaultdict(lambda: StyleEntryDefault)
StyleEntry[XoneStatus.ENTRYHIT] = {
    "background-color": "",
    "color": "black",
    "border": "3px black solid",
    "border-radius": "10px",
    "font-size": "20px",
    "text-align": "center"
}
StyleEntry[XoneStatus.ENTRY] = {
    "background-color": "yellow",
    "color": "black",
    "border": "",
    "border-radius": "10px",
    "font-size": "20px",
    "text-align": "center"
}

StyleStoplossDefault = {
    "background-color": "",
    "color": "red",
    "border": "",
    "border-radius": "10px",
    "font-size": "20px",
    "text-align": "center"
}
StyleStoploss = defaultdict(lambda: StyleStoplossDefault)
StyleStoploss[XoneStatus.STOPLOSSHIT] = {
    "background-color": "",
    "color": "red",
    "border": "3px red solid",
    "border-radius": "10px",
    "font-size": "20px",
    "text-align": "center"
}
StyleStoploss[XoneStatus.FAILED] = {
    "background-color": "",
    "color": "red",
    "border": "3px red dashed",
    "border-radius": "10px",
    "font-size": "20px",
    "text-align": "center"

}
StyleStoploss[XoneStatus.STOPLOSS] = {
    "background-color": "red",
    "color": "white",
    "border": "",
    "border-radius": "10px",
    "font-size": "20px",
    "text-align": "center"
}

StyleTargetDefault = {
    "background-color": "",
    "color": "green",
    "border": "",
    "border-radius": "10px",
    "font-size": "20px",
    "text-align": "center"
}
StyleTarget = defaultdict(lambda: StyleTargetDefault)
StyleTarget[XoneStatus.TARGETHIT] = {
    "background-color": "",
    "color": "green",
    "border": "3px green solid",
    "border-radius": "10px",
    "font-size": "20px",
    "text-align": "center"
}
StyleTarget[XoneStatus.MISSED] = {
    "background-color": "",
    "color": "green",
    "border": "3px green dashed",
    "border-radius": "10px",
    "font-size": "20px",
    "text-align": "center"
}
StyleTarget[XoneStatus.TARGET] = {
    "background-color": "green",
    "color": "white",
    "border": "",
    "border-radius": "10px",
    "font-size": "20px",
    "text-align": "center"
}

StyleForceDefault = {
    "background-color": "",
    "color": "white",
    "border": "",
    "border-radius": "10px",
    "font-size": "16px"
}
StyleForce = defaultdict(lambda: StyleForceDefault)

for status in XoneStatus.PENDING:
    StyleForce[status] = {
        "background-color": "green",
        "color": "white",
        "border": "",
        "border-radius": "10px",
        "font-size": "16px"
    }

for status in XoneStatus.OPEN:
    StyleForce[status] = {
        "background-color": "red",
        "color": "white",
        "border": "",
        "border-radius": "10px",
        "font-size": "16px"
    }


DefaultStyle = {
    "background-color": "",
    "color": "black",
    "border": "",
    "border-radius": "10px",
    "font-size": "20px",
    "text-align": "center"
}
StyleDefault = defaultdict(lambda: DefaultStyle)


class Styles:
    Entry = StyleEntry
    Stoploss = StyleStoploss
    Target = StyleTarget
    Force = StyleForce
