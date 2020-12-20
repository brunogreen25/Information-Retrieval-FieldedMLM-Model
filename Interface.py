from tkinter import *
from Fields import Fields
from Evaluation import Evaluation, EvaluationMethods
from import_metadata import import_csv_metadata
from MySearcher import MySearcher
import time
import webbrowser
import settings
from IndexRepository import IndexRepository

# Global settings parameters
metadata_location = settings.metadata_location
index_location = settings.index_location

# Global variables
window = Tk()
smoothing_params = [0.1] * Fields.get_length()
field_params = Fields.get_length() * [round(1 / Fields.get_length(), 3)]
index = None
frame_canvas=None

# Display query results
def display_query_results(result_tuples):
    global frame_canvas

    # Destroy previous canvas
    if frame_canvas != None:
        frame_canvas.destroy()

    # Create a frame for the canvas with non-zero row&column weights
    frame_canvas = Frame(window)
    frame_canvas.grid(row=3, column=1, columnspan=5, sticky='nw')
    frame_canvas.grid_rowconfigure(0, weight=1)
    frame_canvas.grid_columnconfigure(0, weight=1)
    # Set grid_propagate to False to allow 5-by-5 buttons resizing later
    frame_canvas.grid_propagate(False)

    # Add a canvas in that frame
    canvas = Canvas(frame_canvas)
    canvas.grid(row=0, column=0, sticky="news")

    # Link a scrollbar to the canvas
    vsb = Scrollbar(frame_canvas, orient="vertical", command=canvas.yview)
    vsb.grid(row=0, column=1, sticky='ns')
    canvas.configure(yscrollcommand=vsb.set) # Apply scrolling to canvas

    # Create a main-frame to contain the frames
    frame_of_frames = Frame(canvas)
    canvas.create_window((0, 0), window=frame_of_frames, anchor='nw')

    # Add frames to main-frame
    rows = len(result_tuples)
    frames = [Frame() for _ in range(rows)] # it is assigned to frame_of_frames in the for-loop
    urls = list() # Needed to be saved for entering the link
    chars_per_row = 115
    frames_in_canvas = min(4, rows)
    for i in range(rows):
        # Extracting results
        doc_id = result_tuples[i][0]
        score = round(result_tuples[i][1], 5)
        title = metadata[doc_id][Fields.MetaTitle.value]
        abstract = metadata[doc_id][Fields.MetaAbstract.value]
        publish_date = metadata[doc_id][Fields.MetaTime.value]
        authors = metadata[doc_id][Fields.MetaAuthors.value]
        url = metadata[doc_id][Fields.MetaUrl.value]
        urls.append(url)

        # Frame
        frames[i] = Frame(frame_of_frames, highlightbackground='black', highlightthickness=1)
        frames[i].grid(row=i, column=0, sticky='news')

        # Initial config params
        cur_row = 0

        # Title
        def open_title_links(event):
            i = int(event.widget._name[5:])
            url = urls[i]
            for url in url.split(';'):
                webbrowser.open_new(url)
        title_repr = title[:chars_per_row] if len(title) < chars_per_row else title[:chars_per_row]+'...'
        lbl_title = Label(frames[i], text=title_repr, fg='blue', font='bold 10', cursor='hand2', name='label'+str(i))
        lbl_title.grid(row=cur_row, column=0, sticky='w')
        lbl_title.bind('<Button-1>', lambda e: print(i))
        lbl_title.bind('<Button-1>', open_title_links)
        cur_row += 1

        # Score
        lbl_score = Label(frames[i], text='SCORE: ' + str(score))
        lbl_score.grid(row=cur_row, column=0, sticky='w')
        cur_row += 1

        # Abstract
        if abstract != '':
            if len(abstract)>chars_per_row:
                end_sign = '' if abstract[chars_per_row-1]==' ' or abstract[chars_per_row]==' ' else '-' # Add '-' only if the previous or next char is spacebar
            abstract_repr = abstract[:chars_per_row] if len(abstract)<chars_per_row else abstract[:chars_per_row]+end_sign
            lbl_abstract = Label(frames[i], text=abstract_repr)
            lbl_abstract.grid(row=cur_row, column=0, sticky='w')
            cur_row += 1

            if len(abstract)>chars_per_row:
                abstract_repr_2 = abstract[chars_per_row:(chars_per_row*2)] if len(abstract) < chars_per_row else abstract[chars_per_row:(chars_per_row*2)] + '...'
                abstract_repr_2 = abstract_repr_2[1:] if abstract_repr_2[0]==' ' else abstract_repr_2 # Delete first character if it begins with space
                lbl_abstract = Label(frames[i], text=abstract_repr_2)
                lbl_abstract.grid(row=cur_row, column=0, sticky='w')
                cur_row += 1

        # Publish date
        if publish_date != '':
            lbl_date = Label(frames[i], text=publish_date)
            lbl_date.grid(row=cur_row, column=0, sticky='w')
            cur_row += 1

        # Authors
        if authors != '':
            authors_repr = authors[:chars_per_row] if len(authors)<chars_per_row else authors[:chars_per_row]+'...'
            lbl_author = Label(frames[i], text=authors_repr)
            lbl_author.grid(row=cur_row, column=0, sticky='w')
            cur_row += 1

    # Update main-frame idle tasks to let tkinter calculate frames sizes
    frame_of_frames.update_idletasks()

    # Resize the frame of canvas to show 4 frames (or less) and the scrollbar
    column_width = frames[0].winfo_width() if len(frames)!=0 else 0
    first4rows_height = sum([frames[i].winfo_height() for i in range(frames_in_canvas)])
    frame_canvas.config(width=column_width + vsb.winfo_width(),
                        height=first4rows_height)

    # Set the canvas scrolling region
    canvas.config(scrollregion=canvas.bbox("all"))

# region MAIN EVENTS

# Hyperparameters window
def hyperparam_button_click(event):
    global selected_method

    hyperparam_window = Tk()
    hyperparam_window.title("Hyperparameters")
    hyperparam_window.resizable(0, 0)

    Label(hyperparam_window, text="Field weights").grid(row=1, column=0)
    Label(hyperparam_window, text='Smoothing weights').grid(row=2, column=0)

    # Dynamically add text boxes and field names
    fields_num = Fields.get_length()
    smoothing_texts = []
    field_texts = []
    for i in range(1, fields_num+1):
        # Add first row (field names)
        field_name = Fields.get_fields()[i-1].split('/')[-2]
        field_lbl = Label(hyperparam_window, height='1', width='10', text=field_name if field_name != 'metadata' else Fields.get_fields()[i-1].split('/')[-1])
        field_lbl.grid(row=0, column=i)

        # Add second row (mi values)
        tl = Text(hyperparam_window, height='1', width='10')
        tl.grid(row=1, column=i)
        tl.insert(1.0, str(field_params[i-1]))
        field_texts.append(tl)

        # Add third row (gamma values)
        tl = Text(hyperparam_window, height='1', width='10')
        tl.grid(row=2, column=i)
        tl.insert(1.0, str(smoothing_params[i-1]))
        smoothing_texts.append(tl)

    # Display error if all the hyperparameters are not set up correctly
    error_label = Label(hyperparam_window, text='Enter the values and press OK to save them', fg='red')
    error_label.grid(row=3, column=0, columnspan=fields_num+1)

    def display_error(message):
        nonlocal error_label
        error_label['text'] = message

    # Add error label and OK button (and its event)
    def ok_button_clicked(event):
        global smoothing_params, field_params
        smoothing_params = []
        field_params = []

        # Check if everything is ok with smoothing labels
        for smoothing_text in smoothing_texts:
            try:
                smoothing_param = float(smoothing_text.get('1.0', 'end-1c'))
                if smoothing_param < 0 or smoothing_param > 1:
                    display_error("All smoothing parameters must be in range 0-1")
                    return
                smoothing_params.append(smoothing_param)
            except ValueError:
                display_error("All smoothing parameters must be numbers")
                return


        # Check if everything is ok with field labels
        field_param_sum = 0
        for field_text in field_texts:
            try:
                field_param = float(field_text.get('1.0', 'end-1c'))
                field_param_sum += field_param
                field_params.append(field_param)
            except ValueError:
                display_error("All field parameters must be numbers")
                return
        if abs(field_param_sum - 1) > 0.01:
            display_error("The sum of the field parameters must be 1")
            return
        else:
            display_error("Values have been saved!")

    ok_button = Button(hyperparam_window,  text='SAVE', cursor='hand2')
    ok_button.grid(row=4, column=0, columnspan=fields_num+1)
    ok_button.bind('<Button-1>', ok_button_clicked)

    # region Evaluation
    Label(hyperparam_window, text="EVALUATION", font='none 13 bold').grid(row=0, column=fields_num+1, columnspan=2)

    Label(hyperparam_window, text="Method: ").grid(row=1, column=fields_num+1)

    selected_variable = StringVar(hyperparam_window)
    selected_variable.set(EvaluationMethods.PrecisionK.value)
    def changed_value(event):
        global selected_method
        print(event)
        selected_method = event
    option_menu = OptionMenu(hyperparam_window, selected_variable, EvaluationMethods.PrecisionK.value, EvaluationMethods.MAP.value, EvaluationMethods.MRR.value, EvaluationMethods.NDCG.value, command=changed_value)
    option_menu.grid(row=1, column=fields_num+2)

    Label(hyperparam_window, text="K:").grid(row=2, column=fields_num + 1)
    k_tl = Text(hyperparam_window, height='1', width='10')
    k_tl.grid(row=2, column=fields_num + 2)
    k_tl.insert(1.0, '5')

    test_id_textbox = 1
    selected_method = 'Precision_K'
    evaluation = Evaluation(selected_variable.get(), smoothing_params, field_params, index, k_tl.get('1.0', 'end-1c'), test_id=test_id_textbox)
    def perform_eval_button_clicked(event):
        global selected_method
        evaluation.set_parameters(smoothing_params, field_params, selected_method, k_tl.get('1.0', 'end-1c'), test_id = test_id_textbox.get('1.0', 'end-1c'))
        scores = evaluation.evaluate()
        score_lbl1['text'] = str(scores[0])
        score_lbl2['text'] = str(scores[1])

    perform_eval_button = Button(hyperparam_window, text='Perform Evaluation', cursor='hand2')
    perform_eval_button.grid(row=3, column=fields_num+1, columnspan=2)
    perform_eval_button.bind('<Button-1>', perform_eval_button_clicked)

    Label(hyperparam_window, text="Score (relevant=2):").grid(row=4, column=fields_num + 1)
    score_lbl1 = Label(hyperparam_window, text='0.0', font='bold')
    score_lbl1.grid(row=4, column=fields_num + 2)

    Label(hyperparam_window, text="Score (relevant=1,2):").grid(row=5, column=fields_num + 1)
    score_lbl2 = Label(hyperparam_window, text='0.0', font='bold')
    score_lbl2.grid(row=5, column=fields_num + 2)

    Label(hyperparam_window, text="Test ID: ").grid(row=6, column=fields_num + 1)
    test_id_textbox = Text(hyperparam_window, height='1', width='10')
    test_id_textbox.grid(row=6, column=fields_num + 2)
    test_id_textbox.insert(1.0, '1')
    # endregion

# Search results connection to backend
def search_operation(search_bar, max_results, speed_label):
    # Start performance timing
    start_time = time.time()

    # Get query and max results (and check if everything is OK)
    query = search_bar.get('1.0', 'end-1c')
    try:
        if max_results.get('1.0', 'end-1c') != '':
            max_result = int(max_results.get('1.0', 'end-1c'))
            if max_result < 0 or max_result>1000:
                raise ValueError
        else:
            max_result = 50
            max_results.insert(END, "50")
    except ValueError:
        speed_label['text'] = 'Max results must be either a positive integer lower than 1000 or empty (which is considered as infinity)'
        speed_label['fg'] = 'red'
        return

    if query == '':
        speed_label['text'] = 'Query is empty!'
        speed_label['fg'] = 'red'
        return

    # Perform query
    my_search = MySearcher(index, field_params, smoothing_params)
    result_tuples = my_search.search(query, max_result)

    display_query_results(result_tuples)

    # Display performance time
    speed_label['text'] = 'Checked ' + str(len(metadata)) + ' documents in ' + str(round(time.time()-start_time, 5)) + ' seconds.'
    speed_label['fg'] = 'black'
# endregion

# Load heavy data
def load_data():
    global index, metadata
    # Read metadata and index file
    metadata = import_csv_metadata(path_to_file=metadata_location)
    index = IndexRepository(settings.index_instance_location, settings.mongo_database_location, settings.database_name)

# Hyperparameters button
def set_hyperparams_button():
    hyperparam_button = Button(window, text="Set hyperparameters or Perform eval", fg='black', cursor='hand2')
    hyperparam_button.grid(row=0, column=0)
    hyperparam_button.bind("<Button-1>", hyperparam_button_click)

# Search bar
def set_search_bar():
    # Search
    Label(window, text="Search: ", fg='black').grid(row=1, column=1)
    search_bar = Text(window, fg='black', height='1')
    search_bar.grid(row=1, column=2)
    #search_bar.bind('<Return>', lambda e: enter_clicked(search_bar, max_results, speed_label))
    search_button = Button(window, text="SEARCH", fg="black", cursor='hand2')
    search_button.grid(row=1, column=3)
    search_button.bind("<Button-1>", lambda e: search_operation(search_bar, max_results, speed_label))

    # Max results
    Label(window, fg='black', text="Max results:").grid(row=0, column=4)
    max_results = Text(window, fg='black', height='1', width='7')
    max_results.grid(row=1, column=4)

    # Performance speed info
    speed_label = Label(window, text="Speed will be showed here", fg='black', height='1')
    speed_label.grid(row=2, column=2)

# Title
def set_title():
    Label(window, text="CORD SEARCH ENGINE", fg='black', font='none 20 bold').grid(row=0, column=1, columnspan=3)

# Set the window
def set_window():
    window.title("CORD Search Engine")
    window.resizable(0, 0)
    #window.configure(background='grey')

### MAIN
start_time_interval = time.time()
load_data()
print("Data Loaded: "+str(round(time.time()-start_time_interval, 3)))
set_window()
set_title()
set_search_bar()
set_hyperparams_button()


#MAIN LOOP
window.mainloop()