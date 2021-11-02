import pickle
dict = {'one': 1, 'two': 2}
file = open('dump.txt', 'w')
pickle.dump(dict, file)
file.close()

#and to read it again
file = open('dump.txt', 'r')
dict = pickle.load(file)

print(dict)