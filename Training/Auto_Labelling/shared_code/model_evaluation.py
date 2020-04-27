import logging
import pandas as pd

from . import autolabeling, formatting, utils


def evaluate(predictions, gt_path, lookup_path, count_analyzed, count_total, file_header='FileID'):

    gt_df = utils.load_excel(gt_path)
    evaluation = []

    if not(gt_df.empty):

        logging.info("Ground truth loaded.")

        if len(gt_df) > 0 and len(predictions) > 0:

            try:
                for p in predictions:
                    ev = {}
                    ev['file_id'] = p['file_id']
                    ev['count_analyzed'] = count_analyzed
                    ev['count_total'] = count_total
                    ev['fields'] = []
                    row_document = gt_df.loc[gt_df[file_header] == p['file_id']].iloc[0]
                    for f in p['fields']:
                        f['subfields'] = []
                        columns = autolabeling.map_columns(f['label'], lookup_path)
                        
                        for col in columns:
                            subfield = {}
                            subfield['name'] = col
                            if len(columns) > 1:
                                compare_method = autolabeling.lookup_compare(col, lookup_path)
                                sub_text = formatting.find_subtext(f['text'], compare_method)
                                subfield['text'] = sub_text
                            else:
                                subfield['text'] = f['text'].replace('"','')
                            expected_value = str(row_document[col]).replace('"','')
                            expected_value = expected_value.split('\n')[0]
                            subfield['expected'] = expected_value
                            f['subfields'].append(subfield)

                        ev['fields'].append(f)
                    evaluation.append(ev)
                logging.info(evaluation)
            except Exception as e:
                logging.error(f"Error during evaluation: {e}")

    else:
        logging.error(f"Could not load ground truth.")

    return evaluation

def compare(a, b, field_name, lookup_path):
    compare_method = autolabeling.lookup_compare(field_name, lookup_path)
    a = formatting.normalize(a, compare_method)
    b = formatting.normalize(b, compare_method)
    if(a!=b):
        logging.warning(f"Different: {a}, {b}")
    return a == b 

def create_eval_file(evaluation, model_id, lookup_path):
    output = {}
    output['modelId'] = model_id
    output['accuracy'] = {}
    output['precision'] = {}
    output['unlabelled'] = {}
    output['avgAccuracy'] = 0
    output['avgPrecision'] = 0 
    fields = {}
    unlabelled = {}
    mismatches = []

    try:

        index_max_fields = 0
        len_max_fields = 0

        for i in range(len(evaluation)):
            if len(evaluation[i]['fields']) >= len_max_fields:
                len_max_fields = len(evaluation[i]['fields'])
                index_max_fields = i

        df = pd.DataFrame(evaluation[index_max_fields]['fields'])
        labels = df['label'].tolist()
        for label in labels:
            fields[label] = []
            unlabelled[label] = 0

        for result in evaluation:
            for field in result['fields']:

                match = True
                unlabelled_subfield = False
                
                for subfield in field['subfields']:
                    if not(utils.is_valid(subfield['expected'])):
                        unlabelled_subfield = True
                    sub_match = compare(subfield['text'], subfield['expected'], subfield['name'], lookup_path)
                    # Recording mismatches for later review
                    if sub_match == False:
                        mismatch = {}
                        mismatch['fileId'] = result['file_id']
                        mismatch['labelName'] = subfield['name']
                        mismatch['textExtracted'] = subfield['text']
                        mismatch['textExpected'] = subfield['expected']
                        mismatches.append(mismatch)
                        match = False
                if unlabelled_subfield == True:
                    try:
                        unlabelled[field['label']] += 1
                    except:
                        unlabelled[field['label']] = 1
                try:
                    fields[field['label']].append(match)
                except:
                    fields[field['label']] = [match]
                    unlabelled[field['label']] = 0

        accuracies = []
        precisions = []
        for key in fields.keys():
            field = fields[key]
            accuracy = field.count(True)/(len(evaluation) - unlabelled[key])
            precision = field.count(True)/(len(field) - unlabelled[key])
            output['accuracy'][key] = accuracy
            output['precision'][key] = precision
            output['unlabelled'][key] = unlabelled[key]
            accuracies.append(accuracy)
            precisions.append(precision)
        
        if len(accuracies) > 0:
            avg_accuracy = sum(accuracies) / len(accuracies)
            output['avgAccuracy'] = avg_accuracy
        if len(precisions) > 0:
            avg_precision = sum(precisions) / len(precisions)
            output['avgPrecision'] = avg_precision
        
    except Exception as e:
        logging.error(f"Error creating evaluation file: {e}")

    logging.info(output)

    return output, mismatches
