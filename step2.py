# ------------------------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------------------------

import os
import json
import subprocess
import shlex


# ------------------------------------------------------------------------------
# FUNCTIONS
# ------------------------------------------------------------------------------

def generate_sfz_file(output_path, sfz_data):
    with open(output_path, 'w') as f:
        f.write('// ---------------------------------------\n')
        f.write('// DEFINITIONS\n')
        f.write('// ---------------------------------------\n')
        f.write('#define $VOLUME 7\n')
        f.write('#define $PAN 10\n')
        f.write('#define $ATTACK 71\n')
        f.write('#define $RELEASE 72\n')
        f.write('\n')
        f.write('\n')
        f.write('// ---------------------------------------\n')
        f.write('// CONTROLS\n')
        f.write('// ---------------------------------------\n')
        f.write('\n')
        f.write('<control>\n')
        f.write('\n')
        f.write('// all samples are in the folder "samples"\n')
        f.write('default_path=samples/\n')
        f.write('\n')
        f.write('// labels for the controls\n')
        f.write('label_cc$VOLUME=Volume\n')
        f.write('label_cc$PAN=Pan\n')
        f.write('label_cc$ATTACK=Attack\n')
        f.write('label_cc$RELEASE=Release\n')
        f.write('\n')
        f.write('// set initial volume to 100%\n')
        f.write('set_hdcc$VOLUME=1.0\n')
        f.write('\n')
        f.write('// set initial pan at 50%\n')
        f.write('set_hdcc$PAN=0.5\n')
        f.write('\n')
        f.write('// set initial attack control at 0%\n')
        f.write('set_hdcc$ATTACK=0.0\n')
        f.write('\n')
        f.write('// set initial release control at 50%\n')
        f.write('set_hdcc$RELEASE=0.5\n')
        f.write('\n')
        f.write('\n')
        f.write('// ---------------------------------------\n')
        f.write('// GLOBALS\n')
        f.write('// ---------------------------------------\n')
        f.write('\n')
        f.write('<global>\n')
        f.write('ampeg_attack=0 // seconds\n')
        f.write('ampeg_decay=0 // seconds\n')
        f.write('ampeg_sustain=100 //%\n')
        f.write('\n')
        f.write('// full volume control\n')
        f.write('amplitude_oncc$VOLUME=100 // %\n')
        f.write('amplitude_curvecc$VOLUME=4\n')
        f.write('\n')
        f.write('// full pan control\n')
        f.write('pan_oncc$PAN=100 // %\n')
        f.write('pan_curvecc$PAN=1\n')
        f.write('\n')
        f.write('// full-scale for attack control\n')
        f.write('ampeg_release_oncc$ATTACK=0.25 // seconds\n')
        f.write('\n')
        f.write('// full-scale for release control\n')
        f.write('ampeg_release_oncc$RELEASE=2 // seconds\n')
        f.write('\n')
        f.write('\n')
        f.write('// ---------------------------------------\n')
        f.write('// SAMPLES\n')
        f.write('// ---------------------------------------\n')
        f.write('\n')
        f.write('<group>\n')
        f.write('\n')

        for region in sfz_data['regions']:
            f.write("<region> ")
            f.write(f"sample={region['sample_path']} ")
            f.write(f"key={region['key']} ")
            f.write(f"lokey={region['lokey']} hikey={region['hikey']} ")
            f.write(f"lovel={region['lovel']} hivel={region['hivel']} ")
            f.write("\n")



# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------

# Check for projects folder
if not os.path.exists('projects'):
    raise Exception("Projects folder does not exist.")

# Request the user to select a project
projects = [f for f in os.listdir('projects') if os.path.isdir(os.path.join('projects', f))]
if not projects:
    raise Exception("No projects found.")
print("Select a project:")
for idx, project in enumerate(projects):
    print(f"{idx + 1}: {project}")
selected_project_idx = int(input("Enter the number of the project: ")) - 1
selected_project = projects[selected_project_idx]

# Inside that project folder, check for recording.wav or recording.flac file
project_path = os.path.join('projects', selected_project)
recording = None
for ext in ['.wav', '.flac']:
    recording_file = os.path.join(project_path, f"recording{ext}")
    if os.path.exists(recording_file):
        recording = recording_file
        break
if not recording:
    raise Exception("No recording file (recording.wav or recording.flac) found.")
recording_path = recording

# Aggiungi la creazione della sottocartella degli output
samples_folder_name = 'samples'
samples_extension = 'flac'
output_folder = os.path.join(project_path, samples_folder_name)
os.makedirs(output_folder, exist_ok=True)

# Check for the JSON file with the same name as the project
json_file = os.path.join(project_path, 'configuration.json')
if not os.path.exists(json_file):
    raise Exception(f"JSON file configuration.json not found.")

# Process the JSON file
with open(json_file, 'r') as f:
    data = json.load(f)
samples = data.get('samples', [])

# Oggetto unico contenente parametri globali e informazioni delle regioni
sfz_data = {
    'folder': samples_folder_name,
    'ampeg_attack': 0, # seconds
    'ampeg_decay': 0, # seconds
    'ampeg_sustain': 100, # %
    'ampeg_release': 1, # seconds
    'regions': []
}

# Use ffmpeg to create flac files based on sample data
for idx, sample in enumerate(samples, start=1):
    sample_name = sample['sample_name']
    time_start = sample['time_start']
    time_end = sample['time_end'] - time_start
    output_file_name = f"{sample_name}.{samples_extension}"
    sfz_data['regions'].append({
        'sample_path': output_file_name,
        'lokey': sample['note_interval']['first'],
        'hikey': sample['note_interval']['last'],
        'lovel': sample['velocity_interval']['first'],
        'hivel': sample['velocity_interval']['last'],
        'key': sample['note_number']
    })
    ffmpeg_cmd = [
        'ffmpeg', '-i', recording_path,
        '-ss', str(time_start), '-t', str(time_end),
        os.path.join(output_folder, output_file_name)
    ]
    completion_percentage = idx / len(samples) * 100
    print(f"[{completion_percentage:.1f}%] {' '.join(shlex.quote(arg) for arg in ffmpeg_cmd)}")

    # Eseguire il comando ffmpeg e gestire eventuali input utente
    result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, input=b'y\n')
    if result.returncode != 0:
        print(result.stderr.decode('utf-8').strip())

sfz_file = selected_project + ".sfz"
sfz_path = os.path.join(project_path, sfz_file)
generate_sfz_file(sfz_path, sfz_data)

