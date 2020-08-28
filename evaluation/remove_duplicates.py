import json, argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='Filename to remove duplicates in')
    args = parser.parse_args()

    assert '.json' in args.filename

    filename = args.filename.split('.')[0]

    predictions_json = None

    with open('../evaluation/{0}.json'.format(filename)) as json_file:
        predictions_json = json.load(json_file)

    preds = list()
    num_of_dup = 0

    for pred in predictions_json:
        if pred['category'] == 'resource':
            len_before = len(pred['type'])
            pred['type'] = list(dict.fromkeys(pred['type']))
            len_after = len(pred['type'])

            if len_before != len_after:
                num_of_dup+=1

        preds.append(pred)

    with open('../evaluation/{0}_unique.json'.format(filename), 'w') as json_file:
        json.dump(preds, json_file)

    print("Removed duplicates: {0}".format(num_of_dup))