import csv
import os
from datetime import date
import time
import io
import zipfile
import sys
import traceback
import matplotlib.pyplot as plt
import numpy as np
from backend.onshape.onshape import Onshape
from config.settings import CREDS_PATH, API_VERSION, API_BASE

  

def nc1_csv(framesOutput):
    csvList = [["NAME", "PART NUMBER", "DESCRIPTION","PROFILE", "MATERIAL", "QUANTITY", "LENGTH"]]

    for frame in framesOutput:

        #fileName = frame["partName"] + '-' + frame["partNumber"] + '_' + frame["description"] + '_' + 'S355' + '_' + str(frame["qty"]) + '.step'
        fileName = frame.table_info.part_name + '-' + frame.table_info.part_number + '_' + frame.table_info.description + '_' + 'S355' + '_' + str(frame.table_info.qty) #+ '.step'
        NC1PartNumber = frame.table_info.part_number
        frame.cutting_part_number = NC1PartNumber
        #Add the file name to the dictionary for each frame
        frame.file_name= fileName
        #Create the list to write to file
        csvList.append([fileName, frame.cutting_part_number, frame.table_info.description, frame.profile, 'S355-JR', str(frame.table_info.qty), frame.table_info.length])
    output = io.StringIO()
    
    
    
    writer = csv.writer(output)
    writer.writerow(["NC1 HEADER"])
    writer.writerow(["Key", "Value", "ID"])
    writer.writerow(["Order Identification", "", "A"])
    writer.writerow(["Drawing Identification", "", "B"])
    writer.writerow(["Phase Identification", "PART NUMBER", "C"])
    writer.writerow(["Piece Identification", "PART NUMBER", "D"])
    writer.writerow(["Material", "MATERIAL", "E"])
    writer.writerow(["Quantity", "QUANTITY", "F"])
    writer.writerow(["Profile", "DESCRIPTION", "G"])
    writer.writerow(["Code Profile", "PROFILE", "H"])
    writer.writerow([""])

    writer.writerows(csvList)
    writer.writerow([""])
    writer.writerow(["NOTES:"])
    writer.writerow(["1. USE CENTRAL REFERENCE AXIS FOR DIMENSIONS"])
    writer.writerow(["2. SCRIBE PART NUMBER ON EACH PIECE"])
    print('BACKEND: nc1_csv Completed')
    return output.getvalue()


def one_d_bin_packing(updated_parts, save_path):
    # Updated parts list from the provided data using Primitive Part Number and including quantities

    # Available stock lengths in meters, converted to millimeters
    available_stock_lengths = [6.1, 7.5, 9.5, 12.2, 15.5, 18.5]
    available_stock_lengths = [length * 1000 for length in available_stock_lengths]  # Convert to millimeters

    # Default stock length is 7.5 meters (7500 mm)
    default_stock_length = 7500

    # We only want one image per section type (description), so we'll group by Description
    grouped_parts = {}
    for part in updated_parts:
        description = part["Description"]
        if description not in grouped_parts:
            grouped_parts[description] = []
        grouped_parts[description].append(part)


    # Function to find the smallest appropriate stock length if part length exceeds the default
    def find_stock_length(part_length, available_stock_lengths, default_stock_length):
        if part_length <= default_stock_length:
            return default_stock_length
        # Find the smallest available stock length greater than part length
        for stock_length in available_stock_lengths:
            if part_length <= stock_length:
                return stock_length
        return max(available_stock_lengths)  # If all are smaller, return the largest

    # Function to visualize and save each part by description, accounting for dynamic stock length
    def visualize_and_save_grouped_parts(grouped_parts, available_stock_lengths, default_stock_length, save_path):
        for description, parts in grouped_parts.items():
            fig, ax = plt.subplots(figsize=(10, len(parts) * 2))  # Make the figure taller for multiple stocks
            y_level = 0
            x_start = 0
            stock_num = 1
            current_stock_length = default_stock_length

            for part in parts:
                length = part["Length"]
                primitive_part_number = part["Cutting Part Number"]
                qty = int(part["Qty"])

                # Find the appropriate stock length
                current_stock_length = find_stock_length(length, available_stock_lengths, default_stock_length)

                # Loop through the quantity and add the same part multiple times if qty > 1
                for _ in range(qty):
                    if x_start + length > current_stock_length:  # If the part exceeds the stock, move to the next stock
                        y_level += 1
                        x_start = 0
                        stock_num += 1
                        current_stock_length = find_stock_length(length, available_stock_lengths, default_stock_length)

                    # Create a rectangle for each part in the description
                    rect = plt.Rectangle((x_start, y_level), length, 1, edgecolor='black', facecolor=np.random.rand(3,))
                    ax.add_patch(rect)
                    plt.text(x_start + length / 2, y_level + 0.5, f'{primitive_part_number}', ha='center', va='center', color='white', rotation=0)
                    x_start += length

            # Formatting the plot
            ax.set_xlim(0, current_stock_length)
            ax.set_ylim(0, y_level + 1)
            ax.set_xticks(np.arange(0, current_stock_length + 1, 1000))
            ax.set_yticks([])  # No need for y-axis ticks
            plt.title(f'Stock Visualization for {description} (Stock {stock_num})')
            plt.xlabel('Length')
            plt.grid(True)

            # Save the plot to the specified path
            file_path = os.path.join(save_path, f'Stock_{description}.png')
            plt.savefig(file_path)

            # Close the plot to free up memory
            plt.close(fig)

    # Call the function to visualize and "save" the parts by description
    visualize_and_save_grouped_parts(grouped_parts, available_stock_lengths, default_stock_length, save_path)

    # List the files saved to the path
    print(os.listdir(save_path))



def material_quantity_csv(framesOutput):
    today = date.today()
    csvFilename = "Total Material_" + today.strftime("%d") + today.strftime("%m")+ today.strftime("%Y") + ".csv"
    materialsCsv = [["SECTION", "TOTAL LENGTH", "QTY LENGTHS", "PART NUMBERS"]]
    #Crete a CSV table to aid in the manual population of drawing Views
    views_csvFilename = 'Drawing Views_' + today.strftime("%d") + today.strftime("%m")+ today.strftime("%Y") + ".csv"
    viewsCsv = [["PART STUDIO", "PART", "ORIGINAL BODY NAME", "PART NUMBER", "PRIMITIVE PN", "COMPOSITE PN"]]

    # Variable for length per bar
    length_per_bar = 6.0

    # Initialize a dictionary to store total length and part numbers per material
    material_data = {}

    # Process each part to accumulate total length and part numbers
    for frame in framesOutput:
        material = frame.table_info.description
        length = float(frame.table_info.length)
        quantity = frame.quantities.total_qty
        part_number = frame.table_info.part_number

        # Calculate total length with wastage
        total_length = length * quantity * 1.1

        # If material already in the dictionary, update it
        if material in material_data:
            material_data[material]['total_length'] += total_length
            material_data[material]['part_numbers'].append(part_number)
        else:
            material_data[material] = {
                'total_length': total_length,
                'part_numbers': [part_number]
            }
        #Crete a CSV table to aid in the manual population of drawing Views
        #Get the name of the part studio tha the body is created from
        onshape = Onshape(API_BASE, CREDS_PATH, logging=False)
        url = f"/api/{API_VERSION}/documents/d/{frame.document_info.documentId}/{frame.document_info.wvmType}/{frame.document_info.wvmId}/elements"
        query = {"elementId": frame.document_info.elementId}
        studioName = onshape.request('get', url, query=query).json()
        studioName = studioName[0]['name']
        viewsCsv.append([studioName, frame.table_info.part_name, frame.table_info.original_name, frame.table_info.part_number])
   

    # Calculate the number of 7m lengths required
    for material, data in material_data.items():
        #data['num_bars_required'] = round((data['total_length']) / (length_per_bar*1000), 2)
        # Calculate number of bars required, round UP to nearest integer -- https://stackoverflow.com/questions/2356501/how-do-you-round-up-a-number
        data['num_bars_required'] = -(-(data['total_length']) // (length_per_bar*1000))
        # Create the list to write to file
        materialsCsv.append([material, data['total_length'], data['num_bars_required'], '_ '.join(data['part_numbers'])])
    #print(materialsCsv)
    mat_buf = io.StringIO()
    views_buf = io.StringIO()
    
    csv.writer(mat_buf).writerows(materialsCsv)
    csv.writer(views_buf).writerows(viewsCsv)
    print('BACKEND: material_quantity_csv Completed')
    return mat_buf.getvalue(), views_buf.getvalue()

