import re
import json
import math
import sys
import os

VERSION = "v0.1.1"

SM_EXT = ".sm"
SSC_EXT = ".ssc"
FNF_EXT = ".json"
# stepmania editor's default note precision is 1/192
MEASURE_TICKS = 192
BEAT_TICKS = 48
# fnf step = 1/16 note
STEP_TICKS = 12
NUM_COLUMNS = 8





CHART_SCROLLSPEEDS = (2.9,2.5,2.3) #hard, normal, easy
CHART_SINGERS = ("bf","bob","gf") #singers
CHART_NEEDS_VOICES = True

# usage: have a chart with at least 3 diffs, NM HD and IN
# NM is for mustHitSection, if there's a mine on a section (the bright division line on arrowvortex) it will focus on bf
# HD is enemy's side
# IN is bf's side
# Set attributes above on the constants
# The path can detect if it contains the words "_ez" or "_n" as easy and normal, and exports the json with the appropiate postfixes





# borrowed from my Sharktooth code
class TempoMarker:
    def __init__(self, bpm, tick_pos, time_pos):
        self.bpm = float(bpm)
        self.tick_pos = tick_pos
        self.time_pos = time_pos

    def getBPM(self):
        return self.bpm

    def getTick(self):
        return self.tick_pos
        
    def getTime(self):
        return self.time_pos
    
    def timeToTick(self, note_time):
        return int(round(self.tick_pos + (float(note_time) - self.time_pos) * MEASURE_TICKS * self.bpm / 240000))
        
    def tickToTime(self, note_tick):
        return self.time_pos + (float(note_tick) - self.tick_pos) / MEASURE_TICKS * 240000 / self.bpm

# compute the maximum note index step per measure
def measure_gcd(num_set, MEASURE_TICKS):
    d = MEASURE_TICKS
    for x in num_set:
        d = math.gcd(d, x)
        if d == 1:
            return d
    return d

tempomarkers = []

# helper functions for handling global tempomarkers 
def timeToTick(timestamp):
    for i in range(len(tempomarkers)):
        if i == len(tempomarkers) - 1 or tempomarkers[i+1].getTime() > timestamp:
            return tempomarkers[i].timeToTick(timestamp)
    return 0
            
def tickToTime(tick):
    for i in range(len(tempomarkers)):
        if i == len(tempomarkers) - 1 or tempomarkers[i+1].getTick() > tick:
            return tempomarkers[i].tickToTime(tick)
    return 0.0

def tickToBPM(tick):
    for i in range(len(tempomarkers)):
        if i == len(tempomarkers) - 1 or tempomarkers[i+1].getTick() > tick:
            return tempomarkers[i].getBPM()
    return 0.0

def fnf_to_sm(infile):
    chart_jsons = []
    
    # given a normal difficulty .json,
    # try to detect all 3 FNF difficulties if possible
    infile_name, infile_ext = os.path.splitext(infile)
    infile_easy = infile_name + "-easy" + FNF_EXT
    infile_hard = infile_name + "-hard" + FNF_EXT
    
    with open(infile, "r") as chartfile:
        chart_json = json.loads(chartfile.read().strip('\0'))
        chart_json["diff"] = "Medium"
        chart_jsons.append(chart_json)
        
    if os.path.isfile(infile_easy):
        with open(infile_easy, "r") as chartfile:
            chart_json = json.loads(chartfile.read().strip('\0'))
            chart_json["diff"] = "Easy"
            chart_jsons.append(chart_json)
            
    if os.path.isfile(infile_hard):
        with open(infile_hard, "r") as chartfile:
            chart_json = json.loads(chartfile.read().strip('\0'))
            chart_json["diff"] = "Hard"
            chart_jsons.append(chart_json)

    # for each fnf difficulty
    sm_header = ''
    sm_notes = ''
    for chart_json in chart_jsons:
        song_notes = chart_json["song"]["notes"]
        num_sections = len(chart_json["song"]["notes"])
        # build sm header if it doesn't already exist
        if len(sm_header) == 0:
            song_name = chart_json["song"]["song"]
            song_bpm = chart_json["song"]["bpm"]

            # build tempomap
            bpms = "#BPMS:"
            current_bpm = None
            current_tick = 0
            current_time = 0.0
            for i in range(num_sections):
                section = song_notes[i]
                    
                if section.get("changeBPM", 0) != 0:
                    section_bpm = float(section["bpm"])
                elif current_bpm == None:
                    section_bpm = song_bpm
                else:
                    section_bpm = current_bpm
                if section_bpm != current_bpm:
                    tempomarkers.append(TempoMarker(section_bpm, current_tick, current_time))
                    bpms += "{}={},".format(i*4, section_bpm)
                    current_bpm = section_bpm

                # each step is 1/16
                section_num_steps = section["lengthInSteps"]
                # default measure length = 192
                section_length = STEP_TICKS * section_num_steps
                time_in_section = 15000.0 * section_num_steps / current_bpm

                current_time += time_in_section
                current_tick += section_length

            # add semicolon to end of BPM header entry
            bpms = bpms[:-1] + ";\n"

            # write .sm header
            sm_header = "#TITLE:{}\n".format(song_name)
            sm_header += "#MUSIC:{}.ogg;\n".format(song_name)
            sm_header += bpms

        notes = {}
        last_note = 0
        diff_value = 1

        # convert note timestamps to ticks
        for i in range(num_sections):
            section = song_notes[i]
            section_notes = section["sectionNotes"]
            for section_note in section_notes:
                tick = timeToTick(section_note[0])
                note = section_note[1]
                if section["mustHitSection"]:
                    note = (note + 4) % 8
                length = section_note[2]
                print(tick, note, length)
                
                # Initialize a note for this tick position
                if tick not in notes:
                    notes[tick] = [0]*NUM_COLUMNS

                if length == 0:
                    notes[tick][note] = 1
                else:
                    notes[tick][note] = 2
                    # 3 is "long note toggle off", so we need to set it after a 2
                    long_end = timeToTick(section_note[0] + section_note[2])
                    if long_end not in notes:
                        notes[long_end] = [0]*NUM_COLUMNS
                    notes[long_end][note] = 3
                    if last_note < long_end:
                        last_note = long_end

                if last_note <= tick:
                    last_note = tick + 1

        if len(notes) > 0:
            # write chart & difficulty info
            sm_notes += "\n"
            sm_notes += "#NOTES:\n"
            sm_notes += "	  dance-couple:\n"
            sm_notes += "	  :\n"
            sm_notes += "	  {}:\n".format(chart_json["diff"]) # e.g. Challenge:
            sm_notes += "	  {}:\n".format(diff_value)
            sm_notes += "	  :\n" # empty groove radar

            # ensure the last measure has the correct number of lines
            if last_note % MEASURE_TICKS != 0:
                last_note += MEASURE_TICKS - (last_note % MEASURE_TICKS)

            # add notes for each measure
            for measureStart in range(0, last_note, MEASURE_TICKS):
                measureEnd = measureStart + MEASURE_TICKS
                valid_indexes = set()
                for i in range(measureStart, measureEnd):
                    if i in notes:
                        valid_indexes.add(i - measureStart)
                
                noteStep = measure_gcd(valid_indexes, MEASURE_TICKS)

                for i in range(measureStart, measureEnd, noteStep):
                    if i not in notes:
                        sm_notes += '0'*NUM_COLUMNS + '\n'
                    else:
                        for digit in notes[i]:
                            sm_notes += str(digit)
                        sm_notes += '\n'

                if measureStart + MEASURE_TICKS == last_note:
                    sm_notes += ";\n"
                else:
                    sm_notes += ',\n'

    # output simfile
    with open("{}.sm".format(song_name), "w") as outfile:
        outfile.write(sm_header)
        if len(sm_notes) > 0:
            outfile.write(sm_notes)

# get simple header tag value
def get_tag_value(line, tag):
    tag_re = re.compile("#{}:(.+)\\s*;".format(tag))
    re_match = tag_re.match(line)
    if re_match != None:
        value = re_match.group(1)
        return value
    # try again without a trailing semicolon
    tag_re = re.compile("#{}:(.+)\\s*".format(tag))
    re_match = tag_re.match(line)
    if re_match != None:
        value = re_match.group(1)
        return value
    return None

# parse the BPMS out of a simfile
def parse_sm_bpms(bpm_string):
    sm_bpms = bpm_string.split(",")
    bpm_re = re.compile("(.+)=(.+)")
    for sm_bpm in sm_bpms:
        re_match = bpm_re.match(sm_bpm)
        if re_match != None and re_match.start() == 0:
            current_tick = int(round(float(re_match.group(1)) * BEAT_TICKS))
            current_bpm = float(re_match.group(2))
            current_time = tickToTime(current_tick)
            tempomarkers.append(TempoMarker(current_bpm, current_tick, current_time))

def create_fnf_section(section_length = 16,section_bpm = tickToBPM(0),section_must_hit = False,section_alt_anim = False,section_notes = []):
    section = {}
    section["lengthInSteps"] = section_length
    section["bpm"] = section_bpm
    section["changeBPM"] = False
    section["mustHitSection"] = section_must_hit
    section["typeOfSection"] = 0
    section["altAnim"] = section_alt_anim
    section["sectionNotes"] = section_notes
    return section
#end

def sm_to_fnf(infile):
    infile_pathname = os.path.abspath(infile)
    file_postfix = "-hard"
    diff_id = 0
    if "_ez" in infile_pathname:
        file_postfix = "-easy"
        diff_id = 2
    elif "_n" in infile_pathname:
        file_postfix = ""
        diff_id = 1
    title = "Dadbattle"
    needs_voices = True
    fnf_notes = []
    section_number = 0
    has_parse_sm_bpm_been_run_before = False
    enemy_chart = False
    artist = "stage"
    chart_anchor = False
    charts_have_been_analyzed = 0
    largest_section_num_reached = 0
    sections_that_need_to_be_flipped = []
    sections_that_need_to_be_altanim = []
    offset = 0
    cur_bpm = 0
    player_sections = []
    is_medium = False
    with open(infile, "r") as chartfile:
        enemy_chart = False
        line = chartfile.readline()
        while charts_have_been_analyzed < 3:
            value = get_tag_value(line, "TITLE")
            if value != None:
                title = value
                print("Title:",title)
                line = chartfile.readline()
                continue
            value = get_tag_value(line, "ARTIST")
            if value != None and ";" not in value:
                artist = value
                print("Stage:",artist)
                line = chartfile.readline()
                continue
            value = get_tag_value(line, "OFFSET")
            if value != None:
                offset = float(value) * 1000.0 #offset in fnf is in milliseconds as opposed to seconds
                print("Offset:",offset,"milliseconds")
                line = chartfile.readline()
                continue
            value = get_tag_value(line, "BPMS")
            if value != None and not(has_parse_sm_bpm_been_run_before):
                has_parse_sm_bpm_been_run_before = True # i don't think it would run more than once anyway but just to make sure
                bpm_string_array = [value]
                while True: #prepare for shitty workaround for not having do whiles in python
                    line = chartfile.readline()
                    if ";" not in line:
                            bpm_string_array += line #they're gonna have commas at the beginning but that's fine, the parse_sm_bpms() requires them anyway.
                    else:
                        break
                    #end
                #end
                parse_sm_bpms(''.join(bpm_string_array)) #turns the list of bpm strings into one string
                cur_bpm = tickToBPM(0)
                print(str(cur_bpm) + " is the first result of tickToBPM, aka should be intial tempo")

                offset += 0
                while(line.strip() != "#NOTES:"):
                    line = chartfile.readline()
                continue
            
            notes_re = re.compile("^[\\dM][\\dM][\\dM][\\dM]$") #regex for a sm notes row for dance-double or couple

            # TODO support SSC
            # note from vela: i'm not gonna fucking do that idk what ssc even is
            if line.strip() == "#NOTES:":
                
                line = chartfile.readline()
                
                if line.strip() != "dance-single:":
                    line = chartfile.readline()
                    continue
                print("Detected Dance Single Chart")
                chartfile.readline()
                line = chartfile.readline()
                # TODO support difficulties other than Challenge # note from vela: i gave up trying to do that
                if line.strip() not in ("Hard:","Challenge:","Medium:"):
                    line = chartfile.readline()
                    continue
                charts_have_been_analyzed += 1
                enemy_chart = (line.strip() == "Hard:")
                is_medium = (line.strip() == "Medium:")
                print("Detected Valid Chart", "Enemy Chart:", enemy_chart, "Mines Chart:", is_medium)
                chartfile.readline()
                chartfile.readline()
                line = chartfile.readline()
                tracked_holds = {} # for tracking hold notes, need to add tails later
                while line.strip()[0] != ";":
                    mines_amount_in_section = 0
                    measure_notes = []
                    while line.strip()[0] not in (",",";"):
                        if notes_re.match(line.strip()) != None:
                            measure_notes.append(line.strip())
                        line = chartfile.readline()
                    
                    # for ticks-to-time, ticks don't have to be integer :)
                    ticks_per_row = float(MEASURE_TICKS) / len(measure_notes)


                    fnf_section = create_fnf_section(section_bpm = tickToBPM(section_number * MEASURE_TICKS))
                    print(str(fnf_section["bpm"]) + " is the bpm of section " + str(section_number))
                    fnf_section["changeBPM"] = (fnf_section["bpm"] != cur_bpm)
                    cur_bpm = fnf_section["bpm"]



                    section_notes = []
                    for i in range(len(measure_notes)):
                        notes_row = measure_notes[i]
                        for j in range(len(notes_row)):
                            if notes_row[j] in ("1","2","4"):
                                #note = [tickToTime(MEASURE_TICKS * section_number + i * ticks_per_row) - offset, j, 0]
                                note = [tickToTime(MEASURE_TICKS * section_number + i * ticks_per_row), j, 0]
                                section_notes.append(note)
                                if notes_row[j] in ("2","4"):
                                    tracked_holds[j] = note
                            # hold tails
                            elif notes_row[j] == "3":
                                if j in tracked_holds:
                                    note = tracked_holds[j]
                                    del tracked_holds[j]
                                    note[2] = tickToTime(MEASURE_TICKS * section_number + i * ticks_per_row) - offset - note[0]
                            elif notes_row[j] == "M":
                                mines_amount_in_section += 1

                    if mines_amount_in_section in {2,3} and is_medium:
                        sections_that_need_to_be_altanim.append(section_number)
                    #end
                    if mines_amount_in_section in {1,3} and is_medium:
                        sections_that_need_to_be_flipped.append(section_number)
                    fnf_section["sectionNotes"] = section_notes
                    fnf_section["sectionNumber"] = section_number
                    #print(actual_song_notes)
                    if not enemy_chart and not is_medium: #is player
                        if section_number not in sections_that_need_to_be_flipped:
                            for note in fnf_section["sectionNotes"]:
                                note[1] = (note[1] + 4) % 8
                        player_sections.append(fnf_section)
                    elif enemy_chart and not is_medium:
                        if section_number in sections_that_need_to_be_flipped:
                            for note in fnf_section["sectionNotes"]:
                                note[1] = (note[1] + 4) % 8
                        fnf_notes.append(fnf_section)
                    
                    if section_notes:
                        print("The section above me has notes")
                    section_number += 1

                    # don't skip the ending semicolon
                    if line.strip()[0] != ";":
                        line = chartfile.readline()
            line = chartfile.readline()
            print(section_number)
            section_number = 0
            
    # assemble the fnf json

    cursec = 0
    #print(sections_that_need_to_be_flipped)
    while len(fnf_notes) < len(player_sections):
        print("APPENDED TO FNF NOTES")
        fnf_notes.append(create_fnf_section(section_bpm = 105))
        fnf_notes[-1]["sectionNumber"] = cursec
        cursec += 1
    cursec = 0
    #print(player_sections[48])

    for section in fnf_notes:
        p_section_at_cursec = player_sections[cursec]
        p_section_at_cursec_notes = p_section_at_cursec["sectionNotes"]
        if cursec in sections_that_need_to_be_flipped:
            
            section["mustHitSection"] = True
        if cursec in sections_that_need_to_be_altanim:
            section["altAnim"] = True
        if p_section_at_cursec_notes:
            #print("p_section_at_cursec_notes", p_section_at_cursec_notes, "section", section["sectionNumber"])
            #print("section[\"sectionNotes\"]", section["sectionNotes"], "\n")
            print("we just added",cursec, "to", section["sectionNumber"],  "\n", "original section has", section["sectionNotes"], "END OF ORIGINAL, WHAT WE ADDED added\n", p_section_at_cursec_notes, "\n")
            section["sectionNotes"].extend(p_section_at_cursec_notes)
           
        
        cursec += 1
        
    
    chart_json = {}
    chart_json["song"] = {}
    #chart_json["song"]["song"] = title
    chart_json["song"]["song"] = title.lower()
    chart_json["song"]["bpm"] = tempomarkers[0].getBPM()
    chart_json["song"]["needsVoices"] = CHART_NEEDS_VOICES
    chart_json["song"]["player1"] = CHART_SINGERS[0]
    chart_json["song"]["player2"] = CHART_SINGERS[1]
    chart_json["song"]["player3"] = CHART_SINGERS[2]
    chart_json["song"]["stage"] = artist
    chart_json["song"]["speed"] = CHART_SCROLLSPEEDS[diff_id]
    chart_json["song"]["validScore"]= True
    chart_json["song"]["notes"] = fnf_notes
    #chart_json["bpm"] = tempomarkers[0].getBPM()
    #chart_json["sections"] = section_number
    #chart_json["notes"] = fnf_notes
    
    #with open("{}.json".format(title), "w") as outfile:
    with open(title.replace(' ', '-').lower()+file_postfix+".json", "w") as outfile:
        json.dump(chart_json, outfile, sort_keys=False, indent=1)

def usage():
    print("FNF SM converter")
    print("Usage: {} [chart_file]".format(sys.argv[0]))
    print("where [chart_file] is a .json FNF chart or a .sm simfile")
    print("Title: Title of the fnf song it's replacing, Subtitle: players e.g. \"bf,pico\", Credit: Scroll speed, Artist: if there's text here then it needs voices")
    sys.exit(1)

def main():
    infile = sys.argv[1]
    infile_name, infile_ext = os.path.splitext(os.path.basename(infile))
    if infile_ext == FNF_EXT:
        fnf_to_sm(infile)
    elif infile_ext == SM_EXT:
        sm_to_fnf(infile)
    else:
        print("Error: unsupported file {}".format(infile))
        usage()

if __name__ == "__main__":
    main()
