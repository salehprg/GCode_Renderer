import numpy as np
import torch
from .my_resnet import ResnetModel
from scipy.ndimage import zoom

class DefectDetection:
    def __init__(self):
        self.model = ResnetModel()
        pass

    def __get_blocks_outputs__(self, image):
        input_tensor = self.model.preprocess.preprocess(image)

        output_block1 = self.model.block1(input_tensor)
        output_block2 = self.model.block2_out(output_block1)
        output_block3 = self.model.block3_out(output_block2)

        return output_block1, output_block2, output_block3


    def __get_result_and_concat__(self, image, concat_blocks = [1,2,3]):
        output_block1, output_block2, output_block3 = self.__get_blocks_outputs__(image=image)
        concat_array = [output_block1]

        if 1 in concat_blocks:
            concat_array.append(output_block1)
        if 2 in concat_blocks:
            concat_array.append(output_block2)
        if 3 in concat_blocks:
            concat_array.append(output_block3)

        concatenated_output = torch.cat(concat_array, dim=1)

        return output_block1, output_block2, output_block3, concatenated_output
    

    def detect(self, image_real, image_ideal, concat_blocks=[1,2,3]):
        output1_block1, output1_block2, output1_block3, concatenated_output_real = self.__get_result_and_concat__(image_real, concat_blocks=concat_blocks)
        image_concatenated1 = self.model.tensor_to_image(concatenated_output_real)

        output2_block1, output2_block2, output2_block3, concatenated_output_ideal = self.__get_result_and_concat__(image_ideal, concat_blocks=concat_blocks)
        image_concatenated2 = self.model.tensor_to_image(concatenated_output_ideal)

        diff = (concatenated_output_ideal - concatenated_output_real)
        diff[diff < 0] = 0
        distance = torch.sqrt(torch.sum(diff ** 2, dim=1))

        # Convert distance array into numpy array
        distance_np = distance[0].detach().cpu().numpy()  # Remove batch dimension and convert to NumPy
        distance_np_image = (distance_np - distance_np.min()) / (distance_np.max() - distance_np.min()) * 255
        distance_np_image = distance_np_image.astype(np.uint8)

        defect_mask = zoom(distance_np, (image_real.height / distance_np.shape[0], 
                                     image_real.width / distance_np.shape[1]), order=1)
        
        return defect_mask, distance_np_image