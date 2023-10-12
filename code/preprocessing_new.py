# -*- coding: utf-8 -*-
"""Untitled0.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1JDOb8h2RogjSrgNVHkW55d8DJn8PUxhp
"""


import json
import copy
import random
import os
class data_preprocessing():
    def __init__(self, data_json_file, ontology_json_file, subs_slot_percentage, out_file_path, to_mask = 0):

        self.data = self.read_json(data_json_file)
        self.ontology = self.read_json(ontology_json_file)

        self.updated_data = []

        for dialogue in self.data:

            self.correct_turns(dialogue)
            self.remove_non_occuring(dialogue)

        
        if self.check_consistence_slot_sent():
            print("All slot-value pairs that are present in the state are also in at least user or system before substitution")
        else:
            print("Consistency failed before substitution!!!")

        
        all_slot_value_pairs = []
        for dialogue in self.data:
            all_slot_value_pairs.extend(self.return_all_slot_value_pairs(dialogue))
        new_slot_vals = self.return_new_slot_vals(subs_slot_percentage, all_slot_value_pairs)

        self.remove_duplicates(new_slot_vals)

        if to_mask:
            for new_slot in range(len(new_slot_vals)):
                new_slot_vals[new_slot][2] = '[MASK]'

        # for id, dialogue in enumerate(self.data):

        #     was_changed = 0
        #     for new_slot_val in new_slot_vals:
        #         was_changed = max(was_changed, self.substitute_slot_value(dialogue, new_slot_val[0], new_slot_val[1], new_slot_val[2]))
            
        #     if not was_changed:
        #         # print('Dialogue indexed at ', id, ' was not changed.')
        
        for dialogue in self.data:

            self.remove_non_occuring(dialogue)

        if self.check_consistence_slot_sent():
            print("All slot-value pairs that are present in the state are also in at least user or system after substitution")
        else:
            print("Consistency failed after substitution!!!")
        
        self.save(out_file_path)
    
    def check_consistence_slot_sent(self):
        
        consistent = 1
        for dialogue in self.data:
            for turn in dialogue['turns']:
                for slot in turn['state']['turn_slot_values'].keys():
                    if turn['state']['turn_slot_values'][slot] not in turn['user'] and turn['state']['turn_slot_values'][slot] not in turn['system']:
                        consistent = 0
        return consistent

    
    def return_new_slot_vals(self, percent_slots, slot_value_pairs):
        '''
        input: All slot value pairs of a dialogue and the percentage of slots to substitute
        output: [slot, old_val, new_val] for given % of slots selected randomly
        '''

        n_slots = int((len(slot_value_pairs)*percent_slots)/100)
        slots_to_change = random.sample(slot_value_pairs, n_slots)
        
        for slot in slots_to_change:
            slot.append(self.return_random_slot_value(slot[0]))

        return slots_to_change
        

    def read_json(self, name):
        '''
        input: a json file path
        reads a json file as a dictionary
        '''
        f = open(name)
        data = json.load(f)

        return data
    
    def return_all_slot_value_pairs(self, dialogue):
        '''
        input: a dialogue from the dataset
        returns all slot-value pairs of a given dialogue
        '''
        slot_value_pairs = []
        for turn in dialogue['turns']:
            for slot in turn['state']['turn_slot_values'].keys():
                slot_value_pairs.append([slot, turn['state']['turn_slot_values'][slot]])
        
        return slot_value_pairs
    def return_all_slot_value_pairs_data(self):

        slot_value_pairs = []
        for key in self.ontology.keys():
            for slot in self.ontology[key]:
                slot_value_pairs.append([key, slot])

        return slot_value_pairs
    
    
    def substitute_slot_value(self, dialogue, slot, old_value, new_value):
        '''
        replaces a given slot value with a different slot value
        if you dont want this function to edit the original data, pass a deepcopy of your dialogue
        '''
        was_changed = 0
        for turn in dialogue['turns']:
            if slot in turn['state']['slot_values'].keys() and turn['state']['slot_values'][slot] == old_value:
                turn['state']['slot_values'][slot] = new_value
                was_changed = 1
                if old_value in turn['user']:
                    turn['user'] = turn['user'].replace(old_value, new_value)
                if old_value in turn['system']:
                    turn['system'] = turn['system'].replace(old_value, new_value)

        for turn in dialogue['turns']:
            if slot in turn['state']['turn_slot_values'].keys() and turn['state']['turn_slot_values'][slot] == old_value:
                turn['state']['turn_slot_values'][slot] = new_value
                was_changed = 1

                
        return was_changed

    def return_random_slot_value(self, slot):
        '''
        Intput: A slot value
        Output: A random slot value from that slot
        '''

        return random.choice(self.ontology[slot])
    
    def remove_duplicates(self, slot_value_pairs):
        '''
        removes duplicate slot-value pairs from all slot-value pairs 
        '''
        repeat_ind = []

        for i in range(len(slot_value_pairs)):
            if i in repeat_ind:
                continue
            for j in range(i+1, len(slot_value_pairs)):
                if j in repeat_ind:
                    continue
                if slot_value_pairs[i][0] == slot_value_pairs[j][0] and slot_value_pairs[i][1] == slot_value_pairs[j][1]:
                    repeat_ind.append(j)

        repeat_ind.sort()
        repeat_ind.reverse()
        for i in repeat_ind:
            slot_value_pairs.pop(i)
    
    def correct_turns(self, dialogue):
        '''
        removes the slot-value pairs from the state of the current turn that occured in the previous turns
        '''
        cur_state = {}
        for turn in dialogue['turns']:
            cur_slot_value_pairs = []
            for slot in turn['state']['slot_values'].keys():
                if slot in cur_state.keys() and cur_state[slot] == turn['state']['slot_values'][slot] and turn['state']['slot_values'][slot] not in turn['user'] and turn['state']['slot_values'][slot] not in turn['system']:
                    continue
                cur_slot_value_pairs.append([slot, turn['state']['slot_values'][slot]])
                cur_state[slot] = turn['state']['slot_values'][slot]
            
            turn['state']['turn_slot_values'] = {}
            for new_element in cur_slot_value_pairs:
                turn['state']['turn_slot_values'][new_element[0]] = new_element[1]
    
    def remove_non_occuring(self, dialogue):
        '''
        removes the slots that do not occur in the conversation
        '''
        for turn in dialogue['turns']:
            not_there = []
            for slot in turn['state']['turn_slot_values'].keys():
                if turn['state']['turn_slot_values'][slot] not in turn['user'] and turn['state']['turn_slot_values'][slot] not in turn['system']:
                    not_there.append(slot)
            for slot in not_there:
                turn['state']['turn_slot_values'].pop(slot)

    def save(self, path):
        '''
        saves the dictionary as a json at the desired location
        '''
        out_file = open(path, 'w+')
        json.dump(self.data, out_file, indent=4)

if not os.path.exists('data1'):
    os.makedirs('data1')
preprocessed_data = data_preprocessing("data/train_dials.json", "data/ontology.json", 0, "data1/new_train_dials.json")
preprocessed_data = data_preprocessing("data/dev_dials.json", "data/ontology.json", 0, "data1/new_dev_dials.json")
preprocessed_data = data_preprocessing("data/test_dials.json", "data/ontology.json", 0, "data1/new_test_dials.json")
# preprocessed_data = data_preprocessing("data/mwz2.4/train_dials.json", "data/mwz2.4/ontology.json", 0, "data1/new_train_dials.json")
# preprocessed_data = data_preprocessing("data/mwz2.4/dev_dials.json", "data/mwz2.4/ontology.json", 0, "data1/new_dev_dials.json")
