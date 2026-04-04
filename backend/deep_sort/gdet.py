import numpy as np
import cv2
import tensorflow.compat.v1 as tf  # Direct import of the compat layer
tf.disable_v2_behavior()           # Explicitly turn off V2 featuress tf

class ImageEncoder(object):
    def __init__(self, checkpoint_filename, input_name="images", output_name="features"):
        self.session = tf.Session() # Since we imported compat.v1 as tf
        with tf.gfile.GFile(checkpoint_filename, "rb") as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
            
        tf.import_graph_def(graph_def, name="")
        self.input_var = self.session.graph.get_tensor_by_name(input_name + ":0")
        self.output_var = self.session.graph.get_tensor_by_name(output_name + ":0")

    def __call__(self, data_batch):
        out = self.session.run(self.output_var, feed_dict={self.input_var: data_batch})
        return out

def create_box_encoder(model_filename, batch_size=32):
    image_encoder = ImageEncoder(model_filename)

    def encoder(image, boxes):
        image_patches = []
        for box in boxes:
            # Box format: [x, y, w, h]
            x, y, w, h = box.astype(np.int32)
            patch = image[y:y+h, x:x+w]
            patch = cv2.resize(patch, (64, 128))
            image_patches.append(patch)
            
        if not image_patches:
            return np.zeros((0, 128))
            
        return image_encoder(np.array(image_patches))

    return encoder