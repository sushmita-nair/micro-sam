import numpy as np
from scipy.ndimage import binary_dilation


class PointPromptGenerator:
    def __init__(self, n_positive_points, n_negative_points, dilation_strength):
        self.n_positive_points = n_positive_points
        self.n_negative_points = n_negative_points
        self.dilation_strength = dilation_strength

    def __call__(self, gt, gt_id, center_coordinates, bbox_coordinates):
        """
        Parameters:
            gt: True Labels
            gt_id: Instance ID for the Cells
            center_coordinates: Coordinates for the centroid seed of the cell
            bbox_coordinates: Bounding box coordinates around the cell
        """
        coord_list = []
        label_list = []

        # getting the center coordinate as the first positive point
        coord_list.append(tuple(map(int, center_coordinates)))
        label_list.append(1)

        object_mask = gt == gt_id + 1  # alloting a label id to obtain the coordinates of desired seeds

        # getting the additional positive points by randomly sampling points from this mask
        n_positive_remaining = self.n_positive_points - 1
        if n_positive_remaining > 0:
            # all coordinates of our current object
            object_coordinates = np.where(object_mask)

            # ([x1, x2, ...], [y1, y2, ...])
            n_coordinates = len(object_coordinates[0])

            if n_coordinates > n_positive_remaining:  # for some cases, there aren't any forground object_coordinates
                # randomly sampling n_positive_remaining_points from these coordinates
                positive_indices = np.random.choice(n_coordinates, replace=False, size=n_positive_remaining)
                for positive_index in positive_indices:
                    positive_coordinates = int(object_coordinates[0][positive_index]), \
                        int(object_coordinates[1][positive_index])

                    coord_list.append(positive_coordinates)
                    label_list.append(1)
            else:
                print(f"{n_coordinates} fg spotted..")

        # getting the negative points
        # for this we do the opposite and we set the mask to the bounding box - the object mask
        # we need to dilate the object mask before doing this: we use scipy.ndimage.binary_dilation for this
        dilated_object = binary_dilation(object_mask, iterations=self.dilation_strength)
        background_mask = np.zeros(gt.shape)
        background_mask[bbox_coordinates[0]:bbox_coordinates[2], bbox_coordinates[1]:bbox_coordinates[3]] = 1
        background_mask = abs(background_mask - dilated_object)
        background_mask = binary_dilation(background_mask, iterations=self.dilation_strength)

        n_negative_remaining = self.n_negative_points
        if n_negative_remaining > 0:
            # all coordinates of our current object
            background_coordinates = np.where(background_mask)

            # ([x1, x2, ...], [y1, y2, ...])
            n_coordinates = len(background_coordinates[0])

            # randomly sample n_positive_remaining_points from these coordinates
            negative_indices = np.random.choice(n_coordinates, replace=False, size=n_negative_remaining)
            for negative_index in negative_indices:
                negative_coordinates = int(background_coordinates[0][negative_index]), \
                    int(background_coordinates[1][negative_index])

                coord_list.append(negative_coordinates)
                label_list.append(0)

        return coord_list, label_list, None, object_mask
