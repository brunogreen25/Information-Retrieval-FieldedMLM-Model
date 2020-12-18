import enum
from MySearcher import MySearcher
import settings
import numpy as np
import matplotlib.pyplot as plt
from pylab import figure
import os

class Evaluation:

    def __init__(self, method, smoothing_params, field_params, index, k='10', test_id='1'):
        self.test_id = test_id
        self.method = method
        self.k = int(k) if k!='' else -1

        self.my_search = MySearcher(index, field_params, smoothing_params)

        self.labels = Evaluation.read_txt(settings.path_to_results)
        # WRITTEN AS:
        #   topic_number : 0/1/2 : list_of_cord_uids
        self.question_dict = Evaluation.read_xml(settings.path_to_topics_xml)
        # WRITTEN AS:
        #   topic_number : question_string

    # region DOCUMENT_PARSING
    @staticmethod
    def read_xml(path_to_xml):
        question_dict = dict()
        with open(path_to_xml) as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                line = line.strip()
                if "<query>" in line:
                    prev_line = lines[i-1]
                    question = line[(line.find('>')+1):(line[1:].find('<')+1)]
                    number_ = prev_line[prev_line.find('"')+1:]
                    number = number_[:number_[1:].find('"')+1]
                    question_dict[number] = question
        return question_dict

    @staticmethod
    def read_txt(path_to_txt):
        results = dict()
        with open(path_to_txt) as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                line = line.strip()
                number = line.split(' ')[0]
                cord_uid = line.split(' ')[2]
                relevance = line.split(' ')[3]
                relevance = relevance if relevance[0] != '-' else relevance[1:]

                if i==0 or number != lines[i-1].split(' ')[0]:
                    results[number] = {
                        '0': list(),
                        '1': list(),
                        '2': list()
                    }
                results[number][relevance].append(cord_uid)
        return results
    # endregion

    def set_parameters(self, smoothing_params, field_params, method, k='10', test_id='1'):
        self.test_id = test_id
        self.my_search.set_field_weights(field_params)
        self.my_search.set_smoothing_weights(smoothing_params)
        self.k = int(k) if k!='' else -1
        self.method = method

    def set_k_number(self, k):
        self.k = int(k)

    def evaluate(self):
        if self.method == EvaluationMethods.PrecisionK.value:
            return self.all_precision_k_eval()
        elif self.method == EvaluationMethods.MAP.value:
            return self.map_eval()
        elif self.method == EvaluationMethods.MRR.value:
            return self.mrr_eval()
        else:
            raise Exception("Requested evaluation method is not implemented in the system.")

    # Not entire conf matrix, does not calculate TN
    def calculate_confusion_matrix(self, k, topic_number):
        question = self.question_dict[str(topic_number)]
        results = self.my_search.search(question, k) if self.k != -1 else self.my_search.search(question)
        labels_2 = self.labels[str(topic_number)]['2']
        labels_1 = self.labels[str(topic_number)]['1']

        TP_relevant = 0
        TP_part_relevant = 0
        FP_relevant = 0
        FP_part_relevant = 0

        for result in results:
            if result[0] in labels_2:
                TP_relevant += 1
            else:
                FP_relevant += 1

            if result[0] in labels_1 or result[0] in labels_2:
                TP_part_relevant += 1
            else:
                FP_part_relevant += 1

        FN_relevant = len(labels_2) - TP_relevant
        FN_part_relevant = len(labels_1) + len(labels_2) - TP_part_relevant

        conf_matrix = np.array([[TP_relevant, TP_part_relevant], [FN_relevant, FN_part_relevant], [FP_relevant, FP_part_relevant]])
        return conf_matrix

    @staticmethod
    def print_results_one_line(test_id, score, k, method_name):
        # Create a directory if one does not exist
        directory = settings.precision_k_directory + '/test_number_' + str(test_id)
        if not os.path.isdir(directory):
            try:
                os.mkdir(directory)
            except OSError:
                print("Creation of the directory %s failed" % path)

        # Save in a file
        file_name = directory + '/k=' + str(k) + '_1=relevant_' + method_name + '.txt'
        with open(file_name, "w") as file:
            file.write('If the score of 1 is considered irrelevant\n')
            file.write(str(score[0]))
            file.write('\nIf the score of 1 is considered relevant\n')
            file.write(str(score[1]))

        print("Document printed")

    def precision_k_eval(self, k, topic_number):
        conf_matrix = self.calculate_confusion_matrix(k, topic_number)
        prec_relevant = conf_matrix[0][0] / (conf_matrix[0][0] + conf_matrix[2][0])
        prec_part_relevant = conf_matrix[0][1] / (conf_matrix[0][1] + conf_matrix[2][1])

        return (prec_relevant, prec_part_relevant)


    def all_precision_k_eval(self):
        max_topic_number = len(self.question_dict)
        k = self.k

        avg_score_1 = 0
        avg_score_2 = 0

        scores = list()
        for topic_number in range(1, max_topic_number + 1):
            score = self.precision_k_eval(k, topic_number)
            scores.append(score)
            avg_score_1 += score[0]
            avg_score_2 += score[1]

            print('Question ' + str(topic_number) + " solved (for k=" + str(k) + ")")

        avg_score_1 /= max_topic_number
        avg_score_2 /= max_topic_number
        scores.append((avg_score_1, avg_score_2))
        print(scores[-1])
        Evaluation.print_results_one_line(self.test_id, scores[-1], k, 'Precision@'+str(k))
        return (round(scores[-1][0], 3), round(scores[-1][1], 3))

    def recall_k_eval(self, k, topic_number):
        conf_matrix = self.calculate_confusion_matrix(k, topic_number)
        recall_relevant = conf_matrix[0][0] / (conf_matrix[0][0] + conf_matrix[1][0])
        recall_part_relevant = conf_matrix[0][0] / (conf_matrix[0][0] + conf_matrix[1][0])

        return (round(recall_relevant,3), round(recall_part_relevant,3))

    def map_eval(self):
        ap_socre_relevant = 0
        ap_score_part_relevant = 0

        for topic_number in range(1, len(self.question_dict)+1):
            precs = list()
            recs = list()
            scores_relevant = list()
            scores_part_relevant = list()

            for k in range(1, self.k+1):
                # Precision
                prec = self.precision_k_eval(k, topic_number)
                precs.append(prec)

                # Recall
                rec = self.recall_k_eval(k, topic_number)
                recs.append(rec)

                print("Answered for question=" + str(topic_number) + ' and k=' + str(k))

                if k==1 or recs[-2][0] < recs[-1][0]:
                    scores_relevant.append(precs[-1][0])
                if k==1 or recs[-2][1] < recs[-1][1]:
                    scores_part_relevant.append(precs[-1][1])

            ap_socre_relevant += sum(scores_relevant) / len(self.labels[self.topic_number]['2'])
            ap_score_part_relevant += sum(scores_part_relevant) / len(self.labels[self.topic_number]['1'] + self.labels[self.topic_number]['2'])

        score = (round(ap_socre_relevant, 3), round(ap_score_part_relevant, 3))
        print(score)
        Evaluation.print_results_one_line(self.test_id, score, self.k, 'map')
        return score

    # Does NOT use k
    def mrr_eval(self):
        questions_size = len(self.question_dict)

        mrr_relevant = 0
        mrr_part_relevant = 0

        for topic_number in range(1, questions_size+1):
            labels_2 = self.labels[str(topic_number)]['2']
            labels_1 = self.labels[str(topic_number)]['1']

            question = self.question_dict[str(topic_number)]
            results = self.my_search.search(question)

            for i, result in enumerate(results):
                if result[0] in labels_2:
                    mrr_relevant += 1 / (i+1)
                    break

            for i, result in enumerate(results):
                if result[0] in labels_1 or result[0] in labels_2:
                    mrr_part_relevant += 1 / (i+1)
                    break

            print("Question " + str(topic_number) + " answered")

        mrr_relevant /= questions_size
        mrr_part_relevant /= questions_size

        score = (round(mrr_relevant, 3), round(mrr_part_relevant, 3))
        print(score)
        Evaluation.print_results_one_line(self.test_id, score, self.k, 'mrr')
        return score


class EvaluationMethods(enum.Enum):
    PrecisionK = 'Precision_K'
    MAP = 'MAP'
    MRR = 'MRR'
