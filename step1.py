# ------------------------------------------------------------------------------
# imports
# ------------------------------------------------------------------------------

import sys
sys.path.insert(0, './lib')
from midiutil.MidiFile import MIDIFile
import math
import json
import os

# ------------------------------------------------------------------------------
# FUNCTIONS
# ------------------------------------------------------------------------------

def get_input(prompt, min_val, max_val, default):
    try:
        user_input = input(prompt)
        if user_input == '':
            print(f"Empty input, setting to default: {default}")
            return default
        value = int(user_input)
        if value < min_val:
            print(f"Value too low, setting to minimum: {min_val}")
            return min_val
        if value > max_val:
            print(f"Value too high, setting to maximum: {max_val}")
            return max_val
        print(f"Valid input, setting to requested: {value}")
        return value
    except ValueError:
        print(f"Invalid input, setting to default: {default}")
        return default


def get_distribution(min, max, number_of_elements, shift):
    pitch = (max - min) / number_of_elements
    distribution = []
    element = math.floor(min + (pitch * shift / 100))
    distribution.append(element)
    while math.floor(element + pitch) <= max:
        element += pitch
        distribution.append(math.floor(element))
    return distribution

def get_intervals(distribution):
    output = []
    first, last = 0, 127
    if len(distribution) < 2:
        output.append ({
            'first': first,
            'last': last
        })
        return output
    i = 0
    while i + 1 < len(distribution):
        last = (distribution[i + 1] + distribution[i]) // 2
        output.append({
            'first': first,
            'last': last
        })
        first = last + 1
        i += 1
    last = 127
    output.append ({
        'first': first,
        'last': last
    })
    return output

def sample_name(pitch, vel):
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (pitch // 12) - 1
    note = note_names[pitch % 12]
    return f'{note}{octave}v{vel}'


# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------

# USER INPUT SECTION

project_name = input('Project name ? ')
if project_name == '':
    project_name = 'untitled'
print(f"project name is {project_name}")
print()
lo, hi, df = 0, 127, 21 # 21 = A0 = lowest note in an 88-key piano
note_min = get_input(f"note_min ? ({lo} - {hi}, default {df}): ", lo, hi, df)
print()
lo, hi, df = note_min, 127, 108 # 108 = C8 = highest note in an 88-key piano
note_max = get_input(f"note_max ? ({lo} - {hi}, default {df}): ", lo, hi, df)
print()
lo, hi = 1, note_max - note_min
df = hi // 3 # 1 sample every 3 notes (every sample gets transposed -1 and +1)
note_layers = get_input(f"note_layers ? ({lo} - {hi}, default {df}): ", lo, hi, df)
print()
lo, hi, df = 1, 127, 5
velocity_layers = get_input(f"velocity_layers ? ({lo} - {hi}, default {df}): ", lo, hi, df)
print()
lo, hi, df = 1, 60, 20
time_sustain = get_input(f"time_sustain [seconds] ? ({lo} - {hi}, default {df}): ", lo, hi, df)
print()
lo, hi, df = 1, 60, 5
time_release = get_input(f"time_release [seconds] ? ({lo} - {hi}, default {df}): ", lo, hi, df)
print()
lo, hi, df = 0, 100, 50
velocity_shift = get_input(f"velocity_shift [%] ? ({lo} - {hi}, default {df}): ", lo, hi, df)
print()

notes_distribution = get_distribution(note_min, note_max, note_layers, 50)
notes_intervals = get_intervals(notes_distribution)
velocity_distribution = get_distribution(0, 127, velocity_layers, velocity_shift)
velocity_intervals = get_intervals(velocity_distribution)


# CREATE PROJECT

if not os.path.exists('projects'):
    os.makedirs('projects')
project_path = os.path.join('projects', project_name)
if not os.path.exists(project_path):
    os.makedirs(project_path)

# PREPARE CONFIGURATION FILE

data_export = {
    'note_min': note_min,
    'note_max': note_max,
    'note_layers': note_layers,
    'velocity_layers': velocity_layers,
    'velocity_shift': velocity_shift,
    'time_sustain': time_sustain,
    'time_release': time_release,
    'notes_distribution': notes_distribution,
    'velocity_distribution': velocity_distribution,
    'samples': []
}



# CREATE MIDI FILE

mf = MIDIFile(numTracks=1, file_format=2)
track = 0
channel = 0
time = 0

# 120 bpm -> 1 beat = 0.5 second
mf.addTempo(track, time, 60) 
# initial silence
time += time_release
# repeat addTempo() to enforce a tempo map to be saved in file
# 60 bpm -> 1 beat = 1 second
mf.addTempo(track, time, 60)

# write notes
note_counter = 0
for note in notes_distribution:
    vel_counter = 0
    for vel in velocity_distribution:
        mf.addNote(track, channel, note, time, time_sustain, vel)
        data_export['samples'].append({
            'sample_name': sample_name(note, vel),
            'note_number': note,
            'velocity': vel,
            'time_start': time,
            'time_end': time + time_sustain + time_release,
            'note_interval': notes_intervals[note_counter],
            'velocity_interval': velocity_intervals[vel_counter]
        })
        time += time_sustain
        time += time_release
        vel_counter += 1
    note_counter += 1

# write it to disk
file_name = os.path.join(project_path, 'midi_notes.mid')
with open(file_name, 'wb') as outf:
    mf.writeFile(outf)

# SAVE CONFIGURATION FILE

file_name = os.path.join(project_path, 'configuration.json')
with open(file_name, 'w') as file:
    json.dump(data_export, file)

sys.exit() 

# ------------------------------------------------------------------------------
# END
# ------------------------------------------------------------------------------