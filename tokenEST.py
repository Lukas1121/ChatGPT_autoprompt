import tiktoken

text = """
\\lettercontent{Jeg skriver for at udtrykke min interesse i stillingen som Sundheds-IT konsulent. Med en baggrund inden for nanoscience med specialisering i bio- og strålefysik samt erfaring inden for konsulentarbejde og IT-support, er jeg begejstret for muligheden for at blive en del af jeres team og bidrage til udviklingen af jeres kliniske afdelinger.}

\\lettercontent{Som grundlægger og hoved IT-konsulent hos ZeppelinTech Solutions har jeg udviklet skræddersyede softwareløsninger, herunder et Python-værktøj til forbedret røntgendataanalyse for ESRF. Dette projekt er en del af easistrain-pakken på GitHub og demonstrerer min evne til hurtigt at lære og integrere nye teknologier for at imødekomme specifikke kundebehov.}

\\lettercontent{Under min praktik hos Dansk Teknologisk Institut optimerede jeg arbejdsprocesser ved at udvikle Python-scripts til datakonvertering og behandling. Jeg har også praktisk erfaring med Bash-scripting, Linux-miljøer og GitHub til versionskontrol. Disse erfaringer har givet mig en stærk fundament i at identificere og implementere optimeringsopgaver, hvilket vil være værdifuldt i rollen som Sundheds-IT konsulent.}

\\lettercontent{Min uddannelse i nanoscience fra Københavns Universitet med specialisering i bio- og strålefysik har givet mig en dyb forståelse for klinisk dokumentation og sundhedsfaglige arbejdsgange. Jeg har desuden erfaring med projektledelse og implementering af IT-løsninger, hvilket sikrer, at jeg kan planlægge og sikre fremdrift i processer med deltagelse af forskellige aktører.}

\\lettercontent{Jeg er motiveret af at levere optimale løsninger til kliniske afdelinger gennem kundespecifik fejlfinding, problemløsning og undervisning. Min evne til at strukturere, prioritere og tage selvstændigt ansvar for egne opgaver samt mine analytiske evner gør mig i stand til at afdække og beskrive komplekse problemstillinger. Jeg ser frem til muligheden for at arbejde selvstændigt og systematisk for at levere de bedste løsninger for jeres kliniske afdelinger.}

\\lettercontent{Jeg er begejstret for muligheden for at bidrage til jeres teams succes og ser frem til at diskutere, hvordan mine færdigheder og erfaringer matcher jeres behov. Tak fordi I overvejer min ansøgning.}
"""

# Initialize the tokenizer
enc = tiktoken.get_encoding("cl100k_base")

# Tokenize the text
tokens = enc.encode(text)

# Print the number of tokens
print(f"Number of tokens: {len(tokens)}")
