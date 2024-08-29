#!/usr/bin/env python
class FilterModule(object):
    def filters(self):
        return {
            'minio_nvme_ranges': self.minio_nvme_ranges,
        }
    
    def create_ranged_item(self, start, end):
        """Return a formatted string to represent a single NVMe range for MinIO startup script
        
        Keyword arguments:
        start: an integer that represents the start of the range
        end: an integer that represents the end of the range (assumed to be > start)

        Example expected output: "{0...10}"
        """
        return '{' + str(start) + '...' + str(end) + '}'

    def minio_nvme_ranges(self, nvme_devs):
        """Return a list of NVMe ranges for MinIO startup script. If an NVMe dev is not in a range, return the dev raw as an integer
        
        Keyword arguments:
        nvme_devs: A list of NVMe device numbers (integers)

        Example input: [1, 2, 3, 5]
        Example output: ['{1...3}', 5]
        """
        # We need to sort the nvme_devs because we can't assume they'll be given in sorted order
        nvme_devs.sort()
        # Init vars for start and end to track ranges
        start = end = nvme_devs[0]
        # List of ranges to return to Ansible
        range_list = []

        # Iterate through the list of devs in nvme_devs and build the range_list. If a dev is not in a contiguous range, append the dev by itself
        for dev in nvme_devs:
            # start == dev only at the beginning of a range - do nothing in this case
            if start != dev:
                if dev == end + 1:
                    # Set end to dev if dev is sequential in the current range, then move to next dev
                    end = dev
                else:
                    if start == end:
                        # Append end to range_list, because it is not in a contiguous range
                        range_list.append(end)
                    else:
                        # Append the ranged item, because end is the last in a contiguous range
                        range_list.append(self.create_ranged_item(start, end))
                    # Reset start, end, dev, because we just appended to the range_list and need to start a new range
                    start = end = dev
        # We're at the end of iterating through nvme_devs and must append the final range if it exists
        if start == end:
            # Append end to range_list, because it is not in a contiguous range
            range_list.append(end)
        else:
            # Append the final range to range_list
            range_list.append(self.create_ranged_item(start, end))
        
        return range_list
