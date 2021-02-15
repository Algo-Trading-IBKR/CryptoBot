for x in range(0, 9):
    globals()['list%s' % x] = 'Hello'

print(list1)
print(list2)