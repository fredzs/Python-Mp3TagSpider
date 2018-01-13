#


class ListFunc(object):
    @staticmethod
    def compare_2_lists(list1, list2):
        compare_result = False

        if len(list1) == len(list2) > 0:
            for item in list1:
                if item.lower() in [i.lower() for i in list2]:
                    continue
                else:
                    break
            else:
                compare_result = True
        return compare_result
