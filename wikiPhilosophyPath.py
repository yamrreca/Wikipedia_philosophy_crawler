from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.disable(logging.CRITICAL)

def quitarPrimerParentesis(cadena):
    cParentesisDer = 0
    cParentesisIzq = 0
    bandera = False
    lista = cadena.split()
    for elemento in lista[:7]:   #Checa que el paréntesis en efecto esté antes que cierto número de palabras
    	if '(' in elemento:
    		bandera = True
    		break
    if not bandera:
    	return None, None
    for i in range(len(cadena)):
        if cadena[i] == '(':
            if cParentesisIzq == 0:
            	indiceIzq = i
            cParentesisIzq += 1
        elif cadena[i] == ')':
            cParentesisDer += 1
        if cParentesisIzq != 0 and cParentesisIzq == cParentesisDer:
            indiceDer = i
            sinParentesis = cadena[:indiceIzq] + cadena[indiceDer + 2:] #El 2 es porque se debe saltar el ) y el espacio que lo sigue
            elParentesis = cadena[indiceIzq:indiceDer + 1]
            return sinParentesis, elParentesis

try:
	html = urlopen(r'https://en.wikipedia.org/wiki/Special:Random')
except HTTPError:
	print('No se encontró la página')
	exit()

if html == None:
	print('No se encontró el servidor. Wikipedia ha de haberse caído')
	exit()

bsObj = BeautifulSoup(html, features="html.parser")
titulo = bsObj.body.h1.get_text()
print('Artículo inicial:', titulo + '\n')
print('Camino:\n')

for j in range(35):
	mainBody = bsObj.find('div', {'class':'mw-parser-output'})
	bsParrafo = mainBody.findAll('p',{'class':None, 'id':None})
	logging.debug('bsParrafo: %s'%(bsParrafo))
	i = 0
	cLinks = 0 #Contador para checar que los links no estén todos en un paréntesis
	links = []
	elParentesis = None
	parrafoSinParentesis = None
	for i in range(len(bsParrafo)):  #Checa que haya links en el párrafo, y si no se va al siguiente
		logging.debug('Número del párrafo que se está checando por enlaces: %d'%(i + 1))
		try:  #Sí, ya sé que usualmente no se deben meter tantas cosas en el try-except. En los excepts dice por qué esto no es problema aquí
			if bsParrafo[i].parent.name == 'td' or bsParrafo[i].parent.name == 'tr':  #Se asegura de que no esté en una tabla
				continue
			links = bsParrafo[i].findAll("a", href = re.compile("^(/wiki/)((?!:).)*$"))
			if links == []:
				continue
			logging.error(links[0])
			parrafo = bsParrafo[i].get_text()
			try:
				parrafoSinParentesis, elParentesis = quitarPrimerParentesis(parrafo)
			except TypeError:
				print('Error: posiblemente se trate de una página especial (de desambiguación, etc.)')
				exit()
			for link in links:
				logging.info('Texto del link individual: %s'%(link.get_text()))
				logging.info('Tipo de elParentesis: %s y del parrafoSinParentesis: %s'%(type(elParentesis),type(parrafoSinParentesis)))
				if elParentesis == None or parrafoSinParentesis == None:
					pass
				elif link.get_text() in elParentesis and link.get_text() not in parrafoSinParentesis:
					cLinks += 1
					logging.info('cLinks: %d'%(cLinks))
				logging.info('Longitud de links: %d'%(len(links)))
			if cLinks == len(links):
				continue	
			if links[0].parent.attrs['id'] == 'coordinates':  #Algunos artículos de lugares tienen coordenadas en una posición mala
				continue
			else:
				break
		
		except IndexError: #El único elemento que podría lanzar esto es 
			print('El artículo no tiene enlaces. Posible artículo especial (desambiguación, etc.)')
			exit()
		except KeyError: #Si en algún momento sale esto es que falta algún elemento crucial de la página. No importa cuál sea, rompería el programa de todos modos
			break
	try:
		logging.debug('El primer párrafo es: %s'%(parrafo))
		logging.debug('El primer parrafo sin el primer paréntesis es: %s'%(parrafoSinParentesis))
		logging.debug('El parentesis es: %s'%(elParentesis))
	except Exception:
		continue

	if parrafoSinParentesis == None: #Si no se encontró un paréntesis
		logging.info('No hay paréntesis')
		for link in links:
			if link.get_text() in parrafo and link.get_text() != '':
				nuevoLink = 'https://en.wikipedia.org' + link['href']
				break
	else:
		logging.info('Sí hay paréntesis')
		for link in links:
			if link.get_text() in elParentesis and link.get_text() not in parrafoSinParentesis:
				if link.get_text() != '':
					continue
			elif link.get_text() in parrafoSinParentesis and link.get_text() != '':
				nuevoLink = 'https://en.wikipedia.org' + link['href']
				break

	assert nuevoLink[30:] != None, 'El link no se detectó en el artículo.'

	try:
		html = urlopen(nuevoLink)
	except HTTPError:
		print('No se encontró la página número %d'&(i + 1))
		exit()

	if html == None:
		print('No se encontró el servidor. Wikipedia ha de haberse caído')
		exit()

	bsObj = BeautifulSoup(html, features="html.parser")
	titulo = bsObj.body.h1.get_text()
	print('%d.- %s'%(j + 1, titulo))

	if titulo == 'Philosophy':
		print('Se llegó a filosofía.')
		exit()
	elif titulo == 'Mathematics': #Este artículo ocasiona un ciclo infinito
		print('Matemáticas también cuenta, ¿verdad?')
		exit()

print('No se logró llegar a filosofía en 50 artículos. Deteniendo búsqueda.')