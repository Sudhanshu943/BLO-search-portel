import re

def krutidev_to_unicode(text):
    if not text: return ""
    
    array_one = ["ñ","Q+Z","sas","aa",")Z","ZZ","‘","’","“","”","å","ƒ","„","…","†","‡","ˆ","‰","Š","‹","¶+","d+","[+k","[+","x+","T+","t+","M+","<+","Q+",";+","j+","u+","Ùk","Ù","ä","–","—","é","™","=kk","f=k","à","á","â","ã","ºz","º","í","{k","{","=","«","Nî","Vî","Bî","Mî","<î","|","K","}","J","Vª","Mª","<ªª","Nª","Ø","Ý","nzZ","æ","ç","Á","xz","#",":","v‚","vks","vkS","vk","v","b±","Ã","bZ","b","m","Å",",s",",","_","ô","d","Dk","D","[k","[","x","Xk","X","Ä","?k","?","³","pkS","p","Pk","P","N","t","Tk","T",">","÷","¥","ê","ë","V","B","ì","ï","M+","<+","M","<",".k",".","r","Rk","R","Fk","F",")","n","/k","èk","/","Ë","è","u","Uk","U","i","Ik","I","Q","¶","c","Ck","C","Hk","H","e","Ek","E",";","¸","j","y","Yk","Y","G","o","Ok","O","'k","'","\"k","\"","l","Lk","L","g","È","z","Ì","Í","Î","Ï","Ñ","Ò","Ó","Ô","Ö","Ø","Ù","Ük","Ü","‚","ks","kS","k","h","q","w","`","s","S","a","¡","%","W","•","·","∙","·","~j","~","\\","+"," ः","^","*","Þ","ß","(","¼","½","¿","À","¾","A","-","&","&","Œ","]","~ ","@"]
    array_two = ["॰","QZ+","sa","a","र्द्ध","Z","\"","\"","'","'","०","१","२","३","४","५","६","७","८","९","फ़्","क़","ख़","ख़्","ग़","ज़्","ज़","ड़","ढ़","फ़","य़","ऱ","ऩ","त्त","त्त्","क्त","दृ","कृ","न्न","न्न्","=k","f=","ह्न","ह्य","हृ","ह्म","ह्र","ह्","द्द","क्ष","क्ष्","त्र","त्र्","छ्य","ट्य","ठ्य","ड्य","ढ्य","द्य","ज्ञ","द्व","श्र","ट्र","ड्र","ढ्र","छ्र","क्र","फ्र","र्द्र","द्र","प्र","प्र","ग्र","रु","रू","ऑ","ओ","औ","आ","अ","ईं","ई","ई","इ","उ","ऊ","ऐ","ए","ऋ","क्क","क","क","क्","ख","ख्","ग","ग","ग्","घ","घ","घ्","ङ","चै","च","च","च्","छ","ज","ज","ज्","झ","झ्","ञ","ट्ट","ट्ठ","ट","ठ","ड्ड","ड्ढ","ड़","ढ़","ड","ढ","ण","ण्","त","त","त्","थ","थ्","द्ध","द","ध","ध","ध्","ध्","ध्","न","न","न्","प","प","प्","फ","फ्","ब","ब","ब्","भ","भ्","म","म","म्","य","य्","र","ल","ल","ल्","ळ","व","व","व्","श","श्","ष","ष्","स","स","स्","ह","ीं","्र","द्द","ट्ट","ट्ठ","ड्ड","कृ","भ","्य","ड्ढ","झ्","क्र","त्त्","श","श्","ॉ","ो","ौ","ा","ी","ु","ू","ृ","े","ै","ं","ँ","ः","ॅ","ऽ","ऽ","ऽ","ऽ","्र","्","?"," ़",":","'","'","“","”",";","(",")","{","}","=","।",".","-"," µ","॰",",","् ","/"]

    modified_text = text
    for i in range(len(array_one)):
        modified_text = modified_text.replace(array_one[i], array_two[i])

    # UP-NIC Logic: Shift "f" (Chhoti ee) to the right
    position_of_i = modified_text.find("f")
    while position_of_i != -1:
        if position_of_i < len(modified_text) - 1:
            char_next_to_i = modified_text[position_of_i + 1]
            char_to_be_replaced = "f" + char_next_to_i
            modified_text = modified_text.replace(char_to_be_replaced, char_next_to_i + "ि")
            position_of_i = modified_text.find("f", position_of_i + 1)
        else:
            break

    # UP-NIC Logic: Shift "Z" (Reph) to the left
    modified_text = "  " + modified_text + "  "
    position_of_R = modified_text.find("Z")
    matra_set = ["ा", "ि", "ी", "ु", "ू", "ृ", "े", "ै", "ो", "ौ", "ं", "ँ"]
    while position_of_R > 0:
        probable_position_of_half_r = position_of_R - 1
        character_at_probable_position_of_half_r = modified_text[probable_position_of_half_r]
        
        while character_at_probable_position_of_half_r in matra_set:
            probable_position_of_half_r -= 1
            character_at_probable_position_of_half_r = modified_text[probable_position_of_half_r]
            
        modified_text = modified_text[:probable_position_of_half_r] + "र्" + modified_text[probable_position_of_half_r:position_of_R] + modified_text[position_of_R+1:]
        position_of_R = modified_text.find("Z")

    return modified_text.strip()


def unicode_to_krutidev(text):
    if not text: return ""
    modified_text = text

    # The Urmila Fix: Move Chhoti Ee BEFORE consonant, then jump Reph AFTER both
    modified_text = re.sub(r'([क-ह])ि', r'f\1', modified_text)
    modified_text = re.sub(r'र्(f?[क-ह][ाीुूृेैोौंँ]*)', r'\1Z', modified_text)

    u_chars = [
        "द्र", "द्ध", "क्ष्", "क्ष", "त्र्", "त्र", "ज्ञ", "श्र", "प्र", "क्र", "ट्र", "ड्र",
        "ऑ", "ओ", "औ", "आ", "अ", "ईं", "ई", "इ", "उ", "ऊ", "ऐ", "ए", "ऋ",
        "क्क", "क्", "क", "ख्", "ख", "ग्", "ग", "घ्", "घ", "ङ",
        "चै", "च्", "च", "छ", "ज्", "ज", "झ्", "झ", "ञ",
        "ट्ट", "ट्ठ", "ट", "ठ", "ड्ड", "ड्ढ", "ड", "ढ", "ण्", "ण",
        "त्", "त", "थ्", "थ", "द", "ध्", "ध", "न्", "न",
        "प्", "प", "फ्", "फ", "ब्", "ब", "भ्", "भ", "म्", "म",
        "य्", "य", "र", "ल्", "ल", "ळ", "व्", "व", "श्", "श", "ष्", "ष", "स्", "स", "ह",
        "ीं", "्र", "्य", "ॉ", "ो", "ौ", "ा", "ी", "ु", "ू", "ृ", "े", "ै", "ं", "ँ", "ः", "ॅ", "ऽ", "्", "़", ":"
    ]
    
    k_chars = [
        "æ", ")", "{", "{k", "«", "=", "K", "J", "ç", "Ø", "Vª", "Mª",
        "v‚", "vks", "vkS", "vk", "v", "b±", "bZ", "b", "m", "Å", ",s", "s", "_.k",
        "Dk", "D", "d", "[", "[k", "X", "x", "Ä", "?k", "³",
        "pkS", "P", "p", "N", "T", "t", ">~", ">", "¥",
        "V", "B", "V", "B", "M", "<", "M", "<", "C", ".k",
        "R", "r", "F", "Fk", "n", "è", "/k", "U", "u",
        "I", "i", "¶", "Q", "C", "c", "H", "Hk", "E", "e",
        "Y", "y", "j", "Y", "y", "G", "O", "o", "'", "'k", "\"", "\"k", "L", "l", "g",
        "h", "z", "î", "‚", "ks", "kS", "k", "h", "q", "w", "`", "s", "S", "a", "¡", "%", "W", "·", "~", "+", ":"
    ]

    for i in range(len(u_chars)):
        modified_text = modified_text.replace(u_chars[i], k_chars[i])

    return modified_text.strip()