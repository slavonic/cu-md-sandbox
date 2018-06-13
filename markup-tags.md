# Список идентификаторов

## Идентификаторы, относящиеся ко всему файлу

* `title` - название службы в файле. 
* `date` - дата, которой соответствует служба (для миней).
* `book` - название книги.

Также в этот раздел могут попадать некоторые другие идентификаторы, которые относятся ко всем текста в данном файле (например, `tone` - глас в Октоихе).

## Идентификаторы верхнего уровня (liturgical)

Обычно это названия служб.

* `v` - вечерня
* `u` - утреня

// скорее всего, ещё появятся:

* `pol` - полунощница
* `(m,v)pov` - (малое, великое) повечерие
* `(1,3,6,9)h` - (1, 3, 6, 9) часы


## Идентификаторы элементов внутри службы (liturgical)

* `stih` - стихи (к стихирам, синаксарю и пр., возможно, стоит размечать внутри соответствующих блоков)
* `bu` - богослужебные (и не только) указания. Могут касаться определенной службы, тогда можно разметить внутри неё: `v/bu`.

### Вечерня

* `gv` - стихиры на "Господи воззвах". Может быть 1 блок стихир, тогда все они размечаются порядковым номером. Если блоков несколько, то сначала ставится номер блока, затем номер стихиры внутри него (`v/gv/1/1` и т.д.). Стихиры на "Слава" и "И ныне" размечаются вне блоков: `v/gv/sl` и `v/gv/th` (`sth`).
* `pr` - прокимен.
* `parem` - паремии, для них указывается порядковый номер: `v/parem/1`.
* `lit` - стихиры на литии (о подробной разметке см. `gv`).
* `sthv` - стихиры на стиховне (о подробной разметке см. `gv`).
* `tr` - тропари, для них также указывается порядковый номер (если тропарей несколько) и слава/и ныне.

### Утреня

* `sed` - седальны по кафизмам, указывается номер стихословия, слава/и ныне: `u/sed/1/sl`.
* `sed_pol` - седален по полиелее.
* `ip` - ипакои.
* `step` - антифоны степенны, указывается номер блока, затем номер отдельного песнопения или слава/и ныне.
* `50ps` - стихира по 50 псалме.
* `can` - канон. Для каждого канона указывается его порядковый номер, внутри него размечаются песни, внутри песни - ирмос и тропари. Если в тексте явно указана "Слава" или богородичен, то вместо номера тропаря - `sl/th`. Таким образом, структура первой песни первого канона может выглядеть так:
** `u/can/1/1/1`
** `u/can/1/1/2`
** `u/can/1/1/sl`
** `u/can/1/1/th`
Кроме того, внутри канона выделяются следующие элементы:
** `sed` - указывается номер канона, номер песни, номер седальна или слава/и ныне: `u/can/1/3/sed_1(sl,th)`.
** `kond` - кондак, предшествующая структура сохраняется: `u/can/1/6/kond`.
** `ikos` - икос, так же, как кондак.
** `syn` - синаксарь, на всякий случай указываем, что по 6 песни: `u/can/1/6/syn`
*** `stih` - стихи синаксаря: `u/can/1/6/syn/stih`
** `ex` - светилен/экзапостиларий, так же может быть с порядковым номером или слава/и ныне.
* `hval` - стихиры на хвалитех (о подробной разметке см. `gv`).
* `sthv` - стихиры на стиховне (о подробной разметке см. `gv`).

## Дополнительные пометы

Указываются отдельно от адресации: `{{liturgical=... tone=... type=...}}`

* `tone` - глас
* `type` - обычно дополнительные характеристики песнопения:
** `anat` - анатолиевы (восточны) стихиры;
** `samogl` - самогласен;
** `evang` - евангельская стихира.
