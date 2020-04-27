from services import ProcessDoc, QueueProcessor

from dotenv import load_dotenv
load_dotenv()


def main():
    process_doc = ProcessDoc()
    queue_processor = QueueProcessor()
    
    msg = ""
    while msg != None:
        msg = queue_processor.get_queue_message_str()
        if msg != None:
            print(f"processing: {msg}")
            process_doc.run(msg)

if __name__ == "__main__":
  main()
