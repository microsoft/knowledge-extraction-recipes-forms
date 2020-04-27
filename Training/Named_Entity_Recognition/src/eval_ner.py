import spacy
from spacy.scorer import Scorer
from spacy.gold import GoldParse


class NerEvaluator(): 

    def _load_baseline(self, model_name):
        """Load scapy pre-trained model for Named Entity Recognition

        Arguments:
            model_name (str): Spacy model name to load

        Returns:
            spacy model object
        """
        nlp = spacy.load(model_name)
        return nlp

    def _run_ner(self, model, data, ent_types):
        """Run the Named Entity Recognition model and return the specified entities types.
        
        Arguments:
            model (spacy model object) -- trained Named Entity Recognition model
            data (str) -- document to extract the named entities from
            ent_types (list) -- list with what entities types to extract
        
        Returns:
            (dict) -- python dictionary containing the entity_text, entity_label
        """
        docs = model(data)
        results = {}

        for ent in docs.ents:
            if ent.label_ in ent_types:
                results[ent.text] = ent.label_

        return results

    def run_ner_baseline(self, model_name, data, ent_types):
        """Run a baseline pre-built spacy Named Entity Recognition model.
        
        Arguments:
            model_name (str)-- named of the pre-built spacy model to use
            data (str) -- document to extract the named entities from
            ent_types (list) -- list with what entities types to extract
        
        Returns:
            (dict) -- python dictionary containing the entity_text, entity_label
        """

        model = self._load_baseline(model_name)
        return(self._run_ner(model, data, ent_types))

    def evaluate_ner(self, model, eval_set, ent_types):
        """Evaluate the performance of a Named Entity model
        
        Arguments:
            model (spacy model object) -- trained Named Entity model to evaluate
            eval_set (list) -- Evaluation set passed in the format 
                                [["<doc_text>",{"entities:[[<start_pos>,<end_pos>,"<ENTITY_TYPE>"],
                                                        [<start_pos>,<end_pos>,"<ENTITY_TYPE>"]]}]]
            ent_types (list) -- list with what entities types to extract
        
        Returns:
            (Spacy.scorer.scores) -- scored metrics for the model 
        """
        
        scorer = Scorer()

        for data, expected_result in eval_set:
            selected_entities = []            
            for ent in expected_result.get('entities'):
                if ent[-1] in ent_types:
                    selected_entities.append(ent)
        
            ground_truth_text = model.make_doc(data)
            ground_truth = GoldParse(ground_truth_text, entities = selected_entities)
            pred_value = model(data)
            scorer.score(pred_value, ground_truth)
        
        return scorer.scores

    def evaluate_ner_baseline(self, model_name, eval_set, ent_types):
        """Evaluate the performance of a pre-built spacy Named Entity model
        
        Arguments:
            model_name (str)-- named of the pre-built spacy model to use
            eval_set (list) -- Evaluation set passed in the format 
                                [["<doc_text>",{"entities:[[<start_pos>,<end_pos>,"<ENTITY_TYPE>"],
                                                        [<start_pos>,<end_pos>,"<ENTITY_TYPE>"]]}]]
            ent_types (list) -- list with what entities types to extract
        
        Returns:
            (Spacy.scorer.scores) -- scored metrics for the model 
        """
        
        model = self._load_baseline(model_name)
        return(self.evaluate_ner(model, eval_set, ent_types))


    def build_training_set(self, ground_truth_path, entity_file):


        # TODO pass OCR results location (standardise this)
        return 0

    def train_ner_model(self):
        return 0