<style>
</style>

# Deeper analysis of roll‑along MASW,

CMP cross‑correlation and pseudo‑2‑D Vs mapping

## Concept of the **roll‑along** workflow (SurfSeis manual and

MASW.com)

- **Why roll‑along?** Conventional MASW uses
   all receivers in a single spread, so the dispersion curve represents an
   average beneath the midpoint of the entire array. To map shear‑wave
   velocity laterally, multiple 1‑D Vs profiles must be extracted along the
   line. Park Seismic explains that **a roll‑along dataset contains multiple
   records with the same source offset** ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAATCAMAAACuuX39AAAAAXNSR0IArs4c6QAAAF1QTFRFAAAAAAAAAAA6AABmADqQAGa2OgA6OgBmOpDbZgAAZjoAZjo6ZrbbZrb/kDoAkDo6kNu2kNvbkNv/tmYAtmY6tmZmtraQtv//25A627Zm2////7Zm/9uQ//+2///b5sjJrAAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAAaklEQVQoU7WOyQ6AIBBDZ1ARF3DBBRXm/z9TMDGORw/21ualLcA/coiaDIrxriejAA7RPnOuAOo0m/dyeHkAy/lIhjpb+d/Q9BVvSH0u3xOylZEkG0e9jCdoXlJgUAFNeCE+BVzfA4uI6gRrYQUFjTtcQQAAAABJRU5ErkJggg==) **and receiver array length** ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAATCAMAAAB1AtffAAAAAXNSR0IArs4c6QAAADlQTFRFAAAAAAAAAAA6ADqQAGa2OgA6Oma2OpDbZgAAZrb/kDoAkNv/tmYA25A62////9uQ/9u2//+2///bhSmYmgAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAARElEQVQYV2NgIAPwMjKyQ7QJcTHzQViCHFAhBn5WbqiZvDBJBh4WqJAgByeUBVbGzwbkgZQJcAG183MwAgETTDthlwEAeuABbjT0BXEAAAAASUVORK5CYII=)[[1]](https://www.masw.com/RollAlongACQ.html#:~:text=To%20generate%20a%202,images%20adversely%20influenced%20by%20the). This uniform geometry minimizes near‑ and far‑field biases and
   is required to generate consistent dispersion images[[2]](https://www.masw.com/RollAlongACQ.html#:~:text=To%20generate%20a%202,cross%20section%20can%20become%20unreliable).
- **Preparing a roll‑along dataset.** Two
   strategies are described:
- **Using a land streamer** – all geophones are
   mounted on a wheeled platform; after each shot the entire array is moved
   by one geophone spacing. This yields multiple records with constant ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAATCAMAAACuuX39AAAAAXNSR0IArs4c6QAAAF1QTFRFAAAAAAAAAAA6AABmADqQAGa2OgA6OgBmOpDbZgAAZjoAZjo6ZrbbZrb/kDoAkDo6kNu2kNvbkNv/tmYAtmY6tmZmtraQtv//25A627Zm2////7Zm/9uQ//+2///b5sjJrAAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAAaklEQVQoU7WOyQ6AIBBDZ1ARF3DBBRXm/z9TMDGORw/21ualLcA/coiaDIrxriejAA7RPnOuAOo0m/dyeHkAy/lIhjpb+d/Q9BVvSH0u3xOylZEkG0e9jCdoXlJgUAFNeCE+BVzfA4uI6gRrYQUFjTtcQQAAAABJRU5ErkJggg==) and ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAATCAMAAAB1AtffAAAAAXNSR0IArs4c6QAAADlQTFRFAAAAAAAAAAA6ADqQAGa2OgA6Oma2OpDbZgAAZrb/kDoAkNv/tmYA25A62////9uQ/9u2//+2///bhSmYmgAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAARElEQVQYV2NgIAPwMjKyQ7QJcTHzQViCHFAhBn5WbqiZvDBJBh4WqJAgByeUBVbGzwbkgZQJcAG183MwAgETTDthlwEAeuABbjT0BXEAAAAASUVORK5CYII=). The method speeds acquisition but signal‑to‑noise can be lower
   because receivers are not spiked[[3]](https://www.masw.com/RollAlongACQ.html#:~:text=A%20roll,recompilation%20approach%20is%20a%20post).
- **Shoot‑through (recompilation)** – a
   conventional fixed 24‑ or 48‑channel array is used. The shot point is
   moved along the line while the array remains stationary. For each shot
   record, the central subset of channels that maintain the desired source
   offset ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAATCAMAAACuuX39AAAAAXNSR0IArs4c6QAAAF1QTFRFAAAAAAAAAAA6AABmADqQAGa2OgA6OgBmOpDbZgAAZjoAZjo6ZrbbZrb/kDoAkDo6kNu2kNvbkNv/tmYAtmY6tmZmtraQtv//25A627Zm2////7Zm/9uQ//+2///b5sjJrAAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAAaklEQVQoU7WOyQ6AIBBDZ1ARF3DBBRXm/z9TMDGORw/21ualLcA/coiaDIrxriejAA7RPnOuAOo0m/dyeHkAy/lIhjpb+d/Q9BVvSH0u3xOylZEkG0e9jCdoXlJgUAFNeCE+BVzfA4uI6gRrYQUFjTtcQQAAAABJRU5ErkJggg==) and array length ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAATCAMAAAB1AtffAAAAAXNSR0IArs4c6QAAADlQTFRFAAAAAAAAAAA6ADqQAGa2OgA6Oma2OpDbZgAAZrb/kDoAkNv/tmYA25A62////9uQ/9u2//+2///bhSmYmgAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAARElEQVQYV2NgIAPwMjKyQ7QJcTHzQViCHFAhBn5WbqiZvDBJBh4WqJAgByeUBVbGzwbkgZQJcAG183MwAgETTDthlwEAeuABbjT0BXEAAAAASUVORK5CYII=) is selected. The front and
   back channels are discarded so that every “sub‑array” has the same length
   and offset[[4]](https://www.masw.com/RollAlongACQ.html#:~:text=Preparation%20of%20Roll,channel%20Acquisition). For example, a 24‑channel array with 5‑ft spacing can be
   recompiled into 12‑channel sub‑arrays to build a roll‑along data set[[5]](https://www.masw.com/RollAlongACQ.html#:~:text=First%2C%20choose%20a%20source%20offset,obtained%20through%20the%20normal%20MASW). This is the workflow implemented in SurfSeis and ParkSEIS. Table
   1 in the manual (not shown) enumerates the shot and channel ranges used
   for each sub‑array.
- **Optimising geometry.** Park Seismic
   emphasises that the receiver array length ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAATCAMAAAB1AtffAAAAAXNSR0IArs4c6QAAADlQTFRFAAAAAAAAAAA6ADqQAGa2OgA6Oma2OpDbZgAAZrb/kDoAkNv/tmYA25A62////9uQ/9u2//+2///bhSmYmgAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAARElEQVQYV2NgIAPwMjKyQ7QJcTHzQViCHFAhBn5WbqiZvDBJBh4WqJAgByeUBVbGzwbkgZQJcAG183MwAgETTDthlwEAeuABbjT0BXEAAAAASUVORK5CYII=) should be about twice the
   investigation depth and that the source offset ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAATCAMAAACuuX39AAAAAXNSR0IArs4c6QAAAF1QTFRFAAAAAAAAAAA6AABmADqQAGa2OgA6OgBmOpDbZgAAZjoAZjo6ZrbbZrb/kDoAkDo6kNu2kNvbkNv/tmYAtmY6tmZmtraQtv//25A627Zm2////7Zm/9uQ//+2///b5sjJrAAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAAaklEQVQoU7WOyQ6AIBBDZ1ARF3DBBRXm/z9TMDGORw/21ualLcA/coiaDIrxriejAA7RPnOuAOo0m/dyeHkAy/lIhjpb+d/Q9BVvSH0u3xOylZEkG0e9jCdoXlJgUAFNeCE+BVzfA4uI6gRrYQUFjTtcQQAAAABJRU5ErkJggg==) is typically half of ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAATCAMAAAB1AtffAAAAAXNSR0IArs4c6QAAADlQTFRFAAAAAAAAAAA6ADqQAGa2OgA6Oma2OpDbZgAAZrb/kDoAkNv/tmYA25A62////9uQ/9u2//+2///bhSmYmgAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAARElEQVQYV2NgIAPwMjKyQ7QJcTHzQViCHFAhBn5WbqiZvDBJBh4WqJAgByeUBVbGzwbkgZQJcAG183MwAgETTDthlwEAeuABbjT0BXEAAAAASUVORK5CYII=); i.e., ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEsAAAATCAMAAADvTQBCAAAAAXNSR0IArs4c6QAAAJZQTFRFAAAAAAAAAAA6AABmADo6ADpmADqQAGa2OgAAOgA6OgBmOjqQOma2OpC2OpDbZgAAZjoAZjo6ZmaQZma2ZpC2ZpDbZrbbZrb/kDoAkDo6kGY6kLbbkNu2kNvbkNv/tmYAtmY6tmZmtpBmtpC2traQttv/tv//25A625Bm27Zm27a22/+22////7Zm/9uQ/9u2//+2///bzFDNlwAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAABQklEQVQ4T+2SW1uDMAyGWxTX6RTnafXIPMyCQqH//8+ZQJuM+lQeL7wzNwtp9vXL2wjxH39OwB6/J+4wUm6cltnT/nmr8h18d/eh6O42dF6eCeFelMyuxxIoQAXDaUja7GZfyl425gAur4JArSRpoS2nTxvQGGtOHzX+32Yh3C3fitUKTJp81134nurqs6AOtDVEX4xZ+IXULh8jKfGKGpXKmUtPWkzLqlHfLplPOR0Qj+uYF2uRLVEuPC8aUfTniGYS33jBHH5GtmVOPIGgCdOuH5iFV9xGvJCJ1yJbZuWl2DJiN6PJmvbmI8mLbLUgZVeEC1OH9wzw3PNbcgfZV7BlcUAzvCM66XCxNKyZ28rBWHqf7VpKeQirGVpguTFQyxaYTVf9Jy16GH7E6LXiz7Sv0Dnf8fvOGVNClB7AbGOi4Qtfdh4hWak7rAAAAABJRU5ErkJggg==)[[6]](https://www.masw.com/OptimumOffsetDispersion.html). The receiver spacing ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAATCAMAAABFjsb+AAAAAXNSR0IArs4c6QAAAGxQTFRFAAAAAAAAAAA6AABmADpmADqQAGa2OgAAOgA6OgBmOjpmOjqQOma2OpDbZgAAZjoAZrbbZrb/kDoAkDo6kGY6kNvbkNv/tmYAtmY6tmaQtpA6tv//25A62//b2////7Zm/9uQ/9u2//+2///bSDwrfwAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAAeElEQVQoU2NgoBdQ4uPFsEqGkQ1dTIFbilUOVVBZWEwGJKbIzyTGIAHEQCDDxiDPLM2gLCkrxCshAFavwCUNFgPJMkLsUhYSBIpzgHVApUA6YWLKIhDDFDhBuhTYgYqVhUWFeBWABgoxQoAggziLGNBAHjRHUSHYAEKaBp+4ZI/2AAAAAElFTkSuQmCC) controls both lateral
   resolution and depth of investigation: to achieve greater depth, ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAATCAMAAABFjsb+AAAAAXNSR0IArs4c6QAAAGxQTFRFAAAAAAAAAAA6AABmADpmADqQAGa2OgAAOgA6OgBmOjpmOjqQOma2OpDbZgAAZjoAZrbbZrb/kDoAkDo6kGY6kNvbkNv/tmYAtmY6tmaQtpA6tv//25A62//b2////7Zm/9uQ/9u2//+2///bSDwrfwAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAAeElEQVQoU2NgoBdQ4uPFsEqGkQ1dTIFbilUOVVBZWEwGJKbIzyTGIAHEQCDDxiDPLM2gLCkrxCshAFavwCUNFgPJMkLsUhYSBIpzgHVApUA6YWLKIhDDFDhBuhTYgYqVhUWFeBWABgoxQoAggziLGNBAHjRHUSHYAEKaBp+4ZI/2AAAAAElFTkSuQmCC) or the number of channels
   must be increased[[7]](https://www.masw.com/RollAlongACQ.html#:~:text=The%20receiver%20spacing%20,channel%20acquisition). If ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAATCAMAAACuuX39AAAAAXNSR0IArs4c6QAAAF1QTFRFAAAAAAAAAAA6AABmADqQAGa2OgA6OgBmOpDbZgAAZjoAZjo6ZrbbZrb/kDoAkDo6kNu2kNvbkNv/tmYAtmY6tmZmtraQtv//25A627Zm2////7Zm/9uQ//+2///b5sjJrAAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAAaklEQVQoU7WOyQ6AIBBDZ1ARF3DBBRXm/z9TMDGORw/21ualLcA/coiaDIrxriejAA7RPnOuAOo0m/dyeHkAy/lIhjpb+d/Q9BVvSH0u3xOylZEkG0e9jCdoXlJgUAFNeCE+BVzfA4uI6gRrYQUFjTtcQQAAAABJRU5ErkJggg==) or ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAATCAMAAAB1AtffAAAAAXNSR0IArs4c6QAAADlQTFRFAAAAAAAAAAA6ADqQAGa2OgA6Oma2OpDbZgAAZrb/kDoAkNv/tmYA25A62////9uQ/9u2//+2///bhSmYmgAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAARElEQVQYV2NgIAPwMjKyQ7QJcTHzQViCHFAhBn5WbqiZvDBJBh4WqJAgByeUBVbGzwbkgZQJcAG183MwAgETTDthlwEAeuABbjT0BXEAAAAASUVORK5CYII=) are not optimised, near‑ or
   far‑field effects can distort the dispersion image[[8]](https://www.masw.com/RollAlongACQ.html#:~:text=investigation%20depth%20%28Zmax%29,accuracy%20of%20the%20overall%20data). Thus each sub‑array must be formed using the same ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAATCAMAAACuuX39AAAAAXNSR0IArs4c6QAAAF1QTFRFAAAAAAAAAAA6AABmADqQAGa2OgA6OgBmOpDbZgAAZjoAZjo6ZrbbZrb/kDoAkDo6kNu2kNvbkNv/tmYAtmY6tmZmtraQtv//25A627Zm2////7Zm/9uQ//+2///b5sjJrAAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAAaklEQVQoU7WOyQ6AIBBDZ1ARF3DBBRXm/z9TMDGORw/21ualLcA/coiaDIrxriejAA7RPnOuAOo0m/dyeHkAy/lIhjpb+d/Q9BVvSH0u3xOylZEkG0e9jCdoXlJgUAFNeCE+BVzfA4uI6gRrYQUFjTtcQQAAAABJRU5ErkJggg==), ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAATCAMAAAB1AtffAAAAAXNSR0IArs4c6QAAADlQTFRFAAAAAAAAAAA6ADqQAGa2OgA6Oma2OpDbZgAAZrb/kDoAkNv/tmYA25A62////9uQ/9u2//+2///bhSmYmgAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAARElEQVQYV2NgIAPwMjKyQ7QJcTHzQViCHFAhBn5WbqiZvDBJBh4WqJAgByeUBVbGzwbkgZQJcAG183MwAgETTDthlwEAeuABbjT0BXEAAAAASUVORK5CYII=) and spacing.

### Data acquisition

and recomposition workflow

1. **Determine desired investigation depth** ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACEAAAATCAMAAAApiJT7AAAAAXNSR0IArs4c6QAAAH5QTFRFAAAAAAAAAAA6AABmADqQAGa2OgAAOgA6OgBmOjoAOjqQOma2OpC2OpDbZgAAZgBmZjoAZjqQZpCQZpC2Zra2Zrb/kDoAkGY6kNv/tmYAtmY6tpA6ttvbttv/tv+2tv//25A625Bm27Zm2////7Zm/7a2/9uQ/9u2//+2///bPTcaaQAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAApUlEQVQoU9WRyxaCMAxEk0KLihREQeILpLXQ//9BS93IOVLWZj2Z3JkA/NEQThO1i8i23iswSbOcaTwoGGUVDm3rbKUV4iuCLkDpVzULUE4CT6kDIJ5yCGX59OUOaSwLdjpj7NopMFW94EMxj0AZdLEa89bslNm0oI/XVM1CUgWag1PYy9Y/gZzdb4VzmjxeN4rv3wqN0UNiRciNYKXkz6TphXN5A1u4C5+2R9jbAAAAAElFTkSuQmCC)**.** Choose receiver spacing ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAATCAMAAABFjsb+AAAAAXNSR0IArs4c6QAAAGxQTFRFAAAAAAAAAAA6AABmADpmADqQAGa2OgAAOgA6OgBmOjpmOjqQOma2OpDbZgAAZjoAZrbbZrb/kDoAkDo6kGY6kNvbkNv/tmYAtmY6tmaQtpA6tv//25A62//b2////7Zm/9uQ/9u2//+2///bSDwrfwAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAAeElEQVQoU2NgoBdQ4uPFsEqGkQ1dTIFbilUOVVBZWEwGJKbIzyTGIAHEQCDDxiDPLM2gLCkrxCshAFavwCUNFgPJMkLsUhYSBIpzgHVApUA6YWLKIhDDFDhBuhTYgYqVhUWFeBWABgoxQoAggziLGNBAHjRHUSHYAEKaBp+4ZI/2AAAAAElFTkSuQmCC) and number of channels ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAATCAMAAAB1AtffAAAAAXNSR0IArs4c6QAAAFdQTFRFAAAAAAAAAABmADpmADqQAGa2OgAAOgA6OgBmOpCQOpDbZjoAZrb/kDoAkGY6kGaQkJC2kNv/tmYAtpBmttv/tv//25A62//b2////7Zm/9uQ/9u2///bjf122wAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAASklEQVQYV2NgoDKQ4WPkkeZm5GJgEBYR4hSQEGORYGCQ4WVlYBACYgYpdkEgjwfIkmQSZZDiEAWyQBKSLOL8QAmgNkk2ZpAgUQAA2xYC3FvqcuIAAAAASUVORK5CYII=) so that array length ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAKEAAAATCAMAAADPjZ36AAAAAXNSR0IArs4c6QAAAMNQTFRFAAAAAAAAAAA6AABmADo6ADpmADqQAGa2OgAAOgA6OgBmOjoAOjo6OjpmOjqQOmaQOma2OpCQOpC2OpDbZgAAZgBmZjoAZjo6ZjqQZmaQZma2ZpCQZpC2ZpDbZra2ZrbbZrb/kDoAkDo6kGY6kGaQkJC2kLbbkNvbkNv/tmYAtmY6tmaQtpA6tpBmtpC2ttvbttv/tv+2tv//25A625Bm27Zm27aQ27a22/+22//b2////7Zm/7a2/9uQ/9u2//+2///bThh0CgAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAACQ0lEQVRIS+1WaVPbMBSUAokNpUBr15SjxSY97BTaNHJosSpH//9XoafDlyzFHzp8QjM5Zvy0b7VvtQlCr+tVAaEAu8gn6UDO1pPq/nsROa0mYrKTaUeZCNeWEYwj9yZ2vNmLyJeprKEHpnYX25A0nIPI9TeFxx9CPPsE3woMq9lrt+PZwq0SzzzsNdY2xIphW0xwMGzErioCLEpT+75CBDbyTHxjRx79x87bwHt3qqry5m+suiKiz8pO761Tl4ICma/ry44csvXuY4V2BmF0Xh0SPJOCi2UaqMHxJU7rxGmGBl+Pmd/lkmudzHK0Ei9YP4FZGc67pmHhUPxRhubgnocP6+Ld18pZ2DDUhyWBtCT/8ZRFq1uDu+37UDpQe8F8jlJoy3z0eSawFI6tczsjxZC93ZhLQ1rdBz6UptAxIf3pXl0L2N21btCaZ9ptFlZfQ1mn1WxvN1pZPiTnypJU+8DFUWKxc8dj3QI+3LnT96GYsWHIl23zP0MfUkEQ+srd1BMZoFLtzBStBQyYLp6+jMdSwxCw1EHkHeB337OINUbsi8BgxCRSEVV77jKL4eo6dVYRJ99F4o7ahV0IgEPIXihrjJKiYp6LxNOjHM5I10U6rwUBiq+T2eclxAhLxLZtGNSJFav2rDtO8rlZGcrv+H37iwgCdfdhI+SFSdCbe8fx+kjeMOqVTkh3L8kiRTRAgiFfvZE/goXnx66L9PhS/20ahkIU0PDfr2Kx3if8Sz6n+OB3jNMCByycXcdBeZRvw0X1DGfuTGc8zDYXAAAAAElFTkSuQmCC)[[7]](https://www.masw.com/RollAlongACQ.html#:~:text=The%20receiver%20spacing%20,channel%20acquisition). Pick source offset ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEMAAAATCAMAAAD8mkC2AAAAAXNSR0IArs4c6QAAAI1QTFRFAAAAAAAAAAA6AABmADo6ADpmADqQAGa2OgAAOgA6OgBmOjoAOma2OpDbZgAAZjoAZjo6ZmaQZma2ZpDbZrbbZrb/kDoAkDo6kLbbkNu2kNvbkNv/tmYAtmY6tmZmtpA6tpC2traQttv/tv//25A625Bm27Zm27a22////7Zm/7aQ/9uQ/9u2//+2///bg6Df4gAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAABMUlEQVQ4T+1Sy1LDMAyUAqEupYGWNLxSHsUJNY79/5+HZCsuzkw7HBhO+CTJ0u5qbYD/8xsOmE2GohE3vsHi6XvVqHJH+XAvxV5hUcfYIB/GoMllrPmGAjN2xJpd7/XZO0AndFbVoIXF8IVMXuwl1DPwd7m2jkTpcjespKelZlfNoo6E4SqRQaTzxwkEvPJsp0phDFKBgTIMOz/s3+aLcGOf+REJBeNTLbC45SadVgF3ndSNtk78yDACRfC0jcvRcTcPVe4GwDb3I1ohOnjGN1RwaYztFFH95ej4R+5HGI+mjC9CGMEOe0WILd2EzD+/JYzULIHBGnp6W6uWASrswswDZw19E7/F4I49ikFvhCWzEsbLAvGc/p6t+K/lX/MkxlTY0fyEjr/EaGm9g/U/ZoYvK8oaaUHpdroAAAAASUVORK5CYII=)[[9]](https://www.masw.com/RollAlongACQ.html#:~:text=First%2C%20choose%20a%20source%20offset,X1%20distance%20ahead%20of%20the).
2. **Acquire field records.** Keep the array
   fixed and shoot at ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAATCAMAAACX3symAAAAAXNSR0IArs4c6QAAAGBQTFRFAAAAAAAAAAA6AABmADpmADqQAGa2OgA6OpCQOpDbZgAAZgA6ZjoAZmaQZrb/kDoAkGY6kJC2kNvbkNv/tmYAtmZmtpBmttv/tv//25A62////7Zm/9uQ/9u2//+2///b/zCyLwAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAAXUlEQVQoU8WPWRKAIAxDgxuCu6DIItz/lrbjEfywP2lfk5kW+KnKKuZ7FIq0DcDpbL8F30wu1hedVJYOsNRG3iJJQ0gRIgywJw8GWc88MmSU5H641+cplnVlPn33ACvxBNUHgbJXAAAAAElFTkSuQmCC) different offsets spaced by ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAATCAMAAABFjsb+AAAAAXNSR0IArs4c6QAAAGxQTFRFAAAAAAAAAAA6AABmADpmADqQAGa2OgAAOgA6OgBmOjpmOjqQOma2OpDbZgAAZjoAZrbbZrb/kDoAkDo6kGY6kNvbkNv/tmYAtmY6tmaQtpA6tv//25A62//b2////7Zm/9uQ/9u2//+2///bSDwrfwAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAAeElEQVQoU2NgoBdQ4uPFsEqGkQ1dTIFbilUOVVBZWEwGJKbIzyTGIAHEQCDDxiDPLM2gLCkrxCshAFavwCUNFgPJMkLsUhYSBIpzgHVApUA6YWLKIhDDFDhBuhTYgYqVhUWFeBWABgoxQoAggziLGNBAHjRHUSHYAEKaBp+4ZI/2AAAAAElFTkSuQmCC); e.g., a 24‑channel array and 13 shot locations produce 13
   records[[10]](https://www.masw.com/RollAlongACQ.html#:~:text=First%2C%20choose%20a%20source%20offset,configurations%20specified%20in%20Table%201).
3. **Form sub‑arrays.** For each shot record,
   discard leading and trailing channels so that the remaining channels span
   length ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAATCAMAAAB1AtffAAAAAXNSR0IArs4c6QAAADlQTFRFAAAAAAAAAAA6ADqQAGa2OgA6Oma2OpDbZgAAZrb/kDoAkNv/tmYA25A62////9uQ/9u2//+2///bhSmYmgAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAARElEQVQYV2NgIAPwMjKyQ7QJcTHzQViCHFAhBn5WbqiZvDBJBh4WqJAgByeUBVbGzwbkgZQJcAG183MwAgETTDthlwEAeuABbjT0BXEAAAAASUVORK5CYII=) starting ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAATCAMAAACuuX39AAAAAXNSR0IArs4c6QAAAF1QTFRFAAAAAAAAAAA6AABmADqQAGa2OgA6OgBmOpDbZgAAZjoAZjo6ZrbbZrb/kDoAkDo6kNu2kNvbkNv/tmYAtmY6tmZmtraQtv//25A627Zm2////7Zm/9uQ//+2///b5sjJrAAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAAaklEQVQoU7WOyQ6AIBBDZ1ARF3DBBRXm/z9TMDGORw/21ualLcA/coiaDIrxriejAA7RPnOuAOo0m/dyeHkAy/lIhjpb+d/Q9BVvSH0u3xOylZEkG0e9jCdoXlJgUAFNeCE+BVzfA4uI6gRrYQUFjTtcQQAAAABJRU5ErkJggg==) behind the source. Repeat
   for all records. The result is a roll‑along dataset of overlapping
   sub‑arrays[[11]](https://www.masw.com/RollAlongACQ.html#:~:text=Preparation%20of%20Roll,channel%20Acquisition). Each sub‑array represents a different midpoint along the line.
4. **Process each sub‑array.** Compute
   dispersion images (FK, FDBF, PS or SS) using standard MASW processing for
   each sub‑array. The resulting dispersion curves are associated with the
   midpoint of the sub‑array.
5. **Invert dispersion curves to 1‑D Vs profiles** (see below). The set of 1‑D profiles along the line will later be
   interpolated to a pseudo‑2‑D cross‑section.

## Common‑Mid‑Point cross‑correlation (CMP‑CC)

- **Purpose.** MASW traditionally averages over
   the entire spread, limiting lateral resolution. The **CMP
   cross‑correlation technique** uses correlations of trace pairs to
   improve lateral resolution and reduce dispersion‑curve smearing. The
   method stacks correlations from receiver pairs that share the same
   midpoint and equal spacing so that phase velocity can be estimated more
   accurately[[12]](https://file.scirp.org/Html/1-1211073_84426.htm#:~:text=The%20Common%20Midpoint%20%28CMP%29%20cross,squares%20approach%20%5B31%5D).
- **Workflow (per shot record):**
- **Cross‑correlation of all trace pairs.** For
   each shot gather, compute the cross‑correlation between every pair of
   geophone traces[[13]](https://file.scirp.org/Html/1-1211073_84426.htm#:~:text=gathers%20is%20as%20follows%3A%20First%2C,are%20stacked%20in%20time%20domain). This correlation function effectively converts each pair into a
   virtual source/receiver at the pair’s midpoint.
- **Sort by common midpoint.** For each
   correlation trace, compute the midpoint index (average of the two channel
   positions). Group correlations having the same midpoint and equal receiver
   spacing[[14]](https://file.scirp.org/Html/1-1211073_84426.htm#:~:text=gathers%20is%20as%20follows%3A%20First%2C,correlation).
- **Stack equal‑spacing correlations.** Within
   each midpoint group, stack correlation traces with identical spacing.
   Stacking reinforces coherent Rayleigh‑wave energy and suppresses noise[[15]](https://file.scirp.org/Html/1-1211073_84426.htm#:~:text=gathers%20is%20as%20follows%3A%20First%2C,utilized%20to%20obtain%20inversion%20of).
- **Generate CMP‑CC gathers.** The stacked
   traces for each midpoint form a **CMP cross‑correlation gather**. Apply
   MASW dispersion‑curve extraction (e.g., FK or PS transform) to each CMP‑CC
   gather to generate phase‑velocity dispersion curves[[15]](https://file.scirp.org/Html/1-1211073_84426.htm#:~:text=gathers%20is%20as%20follows%3A%20First%2C,utilized%20to%20obtain%20inversion%20of).
- **Repeat for all shot records** and average
   the dispersion curves at each midpoint to improve signal‑to‑noise.
- **Inversion using genetic algorithms.** The
   Wadi Fatima case study notes that inversion of dispersion curves can
   be achieved using genetic algorithms (GA) or least‑squares methods[[12]](https://file.scirp.org/Html/1-1211073_84426.htm#:~:text=The%20Common%20Midpoint%20%28CMP%29%20cross,squares%20approach%20%5B31%5D). The article emphasises that GA is robust and stable; it operates
   by evolving populations of candidate models via selection, crossover and
   mutation[[16]](https://file.scirp.org/Html/1-1211073_84426.htm#:~:text=4). After inversion, the 1‑D VS profile is averaged at the midpoint
   to represent the sub‑surface beneath that CMP[[17]](https://file.scirp.org/Html/1-1211073_84426.htm#:~:text=provided%20by%20genetic%20algorithm%20,Figure%206).

## Interpreting 1‑D dispersion curves: forward modelling and inversion

- **Forward modelling (Thomson–Haskell algorithm).** To invert a dispersion curve, a theoretical dispersion curve must
   be computed for candidate layered models. The Thomson–Haskell propagator
   matrix method calculates the Rayleigh‑wave dispersion relation by
   multiplying matrices that propagate stress and displacement through each
   layer; the roots of the resulting secular function yield phase velocities[[18]](https://www.crewes.org/Documents/ResearchReports/2019/CRR201946.pdf#:~:text=techniques%20%28Thom,2019). Searching for roots along the velocity axis for each frequency
   generates a theoretical dispersion curve.
- **Global search algorithms.** Because the
   inverse problem is nonlinear and non‑unique, MASW inversion often uses **global
   optimization**, such as Monte‑Carlo or genetic algorithms. The GA
   evolves a population of candidate VS profiles (layer thicknesses and shear
   velocities) to minimize the misfit between theoretical and observed
   dispersion curves[[19]](https://file.scirp.org/Html/1-1211073_84426.htm#:~:text=4). Simulated annealing or Monte‑Carlo sampling can also be used[[20]](https://www.crewes.org/Documents/ResearchReports/2019/CRR201946.pdf#:~:text=techniques%20%28Thom,2019).
- **Workflow for inversion:**
- **Define parameter space.** Specify layer
   boundaries (number of layers, thickness range) and search bounds for
   shear‑wave velocity and compressional velocity (or Poisson’s ratio).
- **Forward compute dispersion curves.** For
   each candidate model, compute the theoretical phase velocities using the
   Thomson–Haskell matrix method[[18]](https://www.crewes.org/Documents/ResearchReports/2019/CRR201946.pdf#:~:text=techniques%20%28Thom,2019).
- **Define misfit function.** Compute the
   root‑mean‑square error between theoretical and experimental dispersion
   curves.
- **Search.** Use GA or Monte‑Carlo to evolve
   candidate models, retaining those with lower misfit. Terminate after a
   fixed number of iterations or when misfit improvement stalls.
- **Return best‑fit VS profile** and optionally
   the ensemble of near‑best models to assess uncertainty.

## Building pseudo‑2‑D Vs cross‑sections via interpolation

- After obtaining 1‑D VS profiles at multiple sub‑array midpoints, a
   **pseudo‑2‑D cross‑section** is constructed by interpolating the Vs
   values in both depth and horizontal directions. The flexible sub‑array
   study with distributed acoustic sensing (DAS) notes that 2‑D MASW aims to
   produce a pseudo‑2‑D shear‑wave velocity map, and that **these
   cross‑sections are produced by spatially interpolating numerous 1‑D Vs
   profiles extracted from overlapping sub‑arrays along the testing alignment**[[21]](https://www.researchgate.net/publication/364772217_DAS_for_2D_MASW_Imaging_A_Case_Study_on_the_Benefits_of_Flexible_Sub-Array_Processing). Sub‑arrays are collected in a roll‑along configuration or
   recorded simultaneously with DAS, then processed individually[[22]](https://www.researchgate.net/publication/364772217_DAS_for_2D_MASW_Imaging_A_Case_Study_on_the_Benefits_of_Flexible_Sub-Array_Processing#:~:text=of%20shear,subsurface%20%20layering%20%20and).
- **Interpolation technique.** Arrange all
   inverted VS profiles in a 2‑D grid where the horizontal axis is the
   midpoint distance and the vertical axis is depth. Use an interpolation
   method (e.g., linear interpolation, natural‑neighbor interpolation or
   kriging) to estimate Vs at grid points between the midpoints. The
   resulting 2‑D matrix can be displayed as a color‑contour cross‑section.
   The DAS study emphasises that sub‑array length and overlap affect the
   resolution of the pseudo‑2‑D cross‑section[[21]](https://www.researchgate.net/publication/364772217_DAS_for_2D_MASW_Imaging_A_Case_Study_on_the_Benefits_of_Flexible_Sub-Array_Processing); shorter sub‑arrays provide higher lateral resolution but may
   reduce depth penetration.

## Practical steps to implement in **SW_Transform**

1. **Add support for sub‑array selection.***In theory:* Accept parameters specifying desired sub‑array length
   (number of channels) and an offset index relative to the source. For each
   shot gather, select a contiguous block of channels starting at start_index such that the block has
   the chosen length.  
   *In SW_Transform code:* Modify the preprocessing pipeline to take a
   list of channel indices. Use seg2.load_seg2_ar to read the full
   24‑channel record, then slice the time matrix (timematrix) columns to keep only the
   selected channels. The selected sub‑array should be accompanied by the
   correct channel spacing and first‑break delay information.
2. **Generate roll‑along sub‑arrays.***Theory:* Determine the number of sub‑arrays by sliding the selected
   block along the array so that each sub‑array has the same length and
   source offset ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAATCAMAAACuuX39AAAAAXNSR0IArs4c6QAAAF1QTFRFAAAAAAAAAAA6AABmADqQAGa2OgA6OgBmOpDbZgAAZjoAZjo6ZrbbZrb/kDoAkDo6kNu2kNvbkNv/tmYAtmY6tmZmtraQtv//25A627Zm2////7Zm/9uQ//+2///b5sjJrAAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAAaklEQVQoU7WOyQ6AIBBDZ1ARF3DBBRXm/z9TMDGORw/21ualLcA/coiaDIrxriejAA7RPnOuAOo0m/dyeHkAy/lIhjpb+d/Q9BVvSH0u3xOylZEkG0e9jCdoXlJgUAFNeCE+BVzfA4uI6gRrYQUFjTtcQQAAAABJRU5ErkJggg==). For a 24‑channel array with 2‑m spacing, sub‑arrays of length 12
   channels can be generated by discarding the first and last 6 channels for
   the first sub‑array, then discarding channels 1–7 and 7–24 for the second,
   etc. Each sub‑array’s midpoint position increments by 2 m.  
   *In code:* Loop over shot records and, for each shot, create a list
   of sub‑array channel indices based on the chosen n_sub and X_1. For each sub‑array, call the
   existing run_single or run_compare functions with extra_params specifying the selected_channels.
3. **Implement CMP cross‑correlation (optional).**  
   *Theory:* For each shot gather, compute the cross‑correlation between
   all pairs of channels. Group correlations by the average channel index
   (midpoint) and by spacing. Stack correlations within each group to form
   CMP‑CC gathers[[15]](https://file.scirp.org/Html/1-1211073_84426.htm#:~:text=gathers%20is%20as%20follows%3A%20First%2C,utilized%20to%20obtain%20inversion%20of). Apply MASW transform (e.g., FDBF, PS, SS) to the CMP‑CC gather
   to extract dispersion curves.  
   *In code:* Write a function compute_cmpcc_gathers(timematrix) that
   returns a 3‑D array: n_midpoints × n_lags × n_spacing. Use numpy.correlate or scipy.signal.correlate to compute
   correlations. Implement a stacking routine. Then feed each CMP‑CC gather
   into existing processing functions.
4. **Process sub‑arrays or CMP‑CC gathers.** Use
   SW_Transform’s run_single to compute dispersion
   curves for each sub‑array. run_single already supports multiple
   methods (fk, fdbf, ps, ss), vibrosis compensation, and export
   of power spectra. Collect the dispersion picks (frequency vs. phase
   velocity) and save them along with the sub‑array midpoint.
5. **Invert each dispersion curve.**  
   *Implementation options:*

6.      **Integrate
an open‑source inversion module.** Tools like **SWIGA** (Surface Wave Inversion via Genetic Algorithms) or the **MASWaves inversion
toolbox** provide Python code for genetic‑algorithm inversion of dispersion
curves. They implement the Thomson–Haskell forward model and GA search.

7. **Implement simple Monte‑Carlo/GA inversion.** Write code that generates random VS profiles within specified
   bounds, computes the theoretical dispersion curve using a propagator
   matrix (libraries exist, e.g., pyrocko or pyTectonics), and selects the model
   with minimal misfit. Use GA operators (selection, crossover, mutation) to
   evolve the population. Use the Wadi Fatima workflow as a template[[19]](https://file.scirp.org/Html/1-1211073_84426.htm#:~:text=4).
8. **Assemble pseudo‑2‑D Vs cross‑section.***Theory:* Each inverted 1‑D profile corresponds to the midpoint of a
   sub‑array at position ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA0AAAATCAMAAAB86XelAAAAAXNSR0IArs4c6QAAAGBQTFRFAAAAAAAAAAA6AABmADpmADqQAGa2Oma2OpDbZgAAZgBmZjoAZrbbkDoAkDo6kGY6kNvbkNv/tmYAtmY6tmaQtrb/ttu2tv//25A62//b2////7Zm/9uQ/9u2//+2///bHZwGrQAAAAF0Uk5TAEDm2GYAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAAZdEVYdFNvZnR3YXJlAE1pY3Jvc29mdCBPZmZpY2V/7TVxAAAAWElEQVQoU2NgoDeQ5WYSZBAGYhCQF5Hk5RDmQbhBgpEDyUHSzOIInjw/RJM8H5CS5xPg5ZCBahRiEWSQYGSXYpDjZEP2jgSyWQzCECshQI5LTBSJx8kqBQApXwOcuEjRHQAAAABJRU5ErkJggg==). Let VS_i(depth) be the VS values at
   discrete depths for profile i. To build a 2‑D grid, define a
   regular horizontal grid spanning the survey length. At each depth level,
   perform interpolation along the horizontal axis using the discrete VS_i. Linear or natural‑neighbor
   interpolation can be performed using scipy.interpolate.griddata or scipy.interpolate.interp1d. Optionally
   apply smoothing to reduce interpolation artifacts.  
   *In code:* Create an array vs_profiles of shape (n_profiles, n_depths) and a corresponding
   array of midpoints x_mid. Use scipy.interpolate.griddata((x_mid, depth), vs_values, (X_grid,
   Z_grid)) to obtain vs_grid. Plot the result using matplotlib.pyplot.contourf.
9. **Integrate into SW_Transform user interface.** Add GUI and CLI options to specify sub‑array length, source
   offset, and interpolation parameters. Provide options to export 1‑D VS
   profiles and the interpolated 2‑D cross‑section as images or numerical
   grids.

### Additional practical

considerations

- **Resolution
   vs. depth trade‑off.** A shorter sub‑array (fewer
   channels) gives higher lateral resolution but reduces the maximum
   resolvable wavelength and depth of investigation[[7]](https://www.masw.com/RollAlongACQ.html#:~:text=The%20receiver%20spacing%20,channel%20acquisition).
   The user should choose sub‑array length according to target depth.
- **Noise
   and stacking.** Using multiple shots and stacking
   dispersion curves across shots or CMP‑CC gathers improves signal‑to‑noise
   ratio. In vibrosis surveys, frequency‑domain weighting may be applied (as
   already implemented in SW_Transform’s FDBF method).
- **Validation.** Compare the pseudo‑2‑D Vs cross‑section with invasive
   measurements (e.g., Cone Penetration Test data) or other geophysical
   methods, as done in DAS case studies[[23]](https://www.researchgate.net/publication/364772217_DAS_for_2D_MASW_Imaging_A_Case_Study_on_the_Benefits_of_Flexible_Sub-Array_Processing#:~:text=2D%20MASW%20results%20at%20a,study%20site%20and%20evaluate%20those).
- **Open‑source
   resources.** Although SurfSeis is commercial, the
   open‑source MASW inversion tool (MASWaves) provides functions for
   dispersion extraction and inversion that can serve as templates. The
   CMP‑CC implementation described above is not yet available in a Python
   library, so its integration would be a novel contribution.

---

[[1]](https://www.masw.com/RollAlongACQ.html#:~:text=To%20generate%20a%202,images%20adversely%20influenced%20by%20the) [[2]](https://www.masw.com/RollAlongACQ.html#:~:text=To%20generate%20a%202,cross%20section%20can%20become%20unreliable) [[3]](https://www.masw.com/RollAlongACQ.html#:~:text=A%20roll,recompilation%20approach%20is%20a%20post) [[4]](https://www.masw.com/RollAlongACQ.html#:~:text=Preparation%20of%20Roll,channel%20Acquisition) [[5]](https://www.masw.com/RollAlongACQ.html#:~:text=First%2C%20choose%20a%20source%20offset,obtained%20through%20the%20normal%20MASW) [[7]](https://www.masw.com/RollAlongACQ.html#:~:text=The%20receiver%20spacing%20,channel%20acquisition) [[8]](https://www.masw.com/RollAlongACQ.html#:~:text=investigation%20depth%20%28Zmax%29,accuracy%20of%20the%20overall%20data) [[9]](https://www.masw.com/RollAlongACQ.html#:~:text=First%2C%20choose%20a%20source%20offset,X1%20distance%20ahead%20of%20the) [[10]](https://www.masw.com/RollAlongACQ.html#:~:text=First%2C%20choose%20a%20source%20offset,configurations%20specified%20in%20Table%201) [[11]](https://www.masw.com/RollAlongACQ.html#:~:text=Preparation%20of%20Roll,channel%20Acquisition) Roll-Along Format for 2D Cross Section

[Roll-Along Format for 2D Cross Section](https://www.masw.com/RollAlongACQ.html)

[[6]](https://www.masw.com/OptimumOffsetDispersion.html) Optimum Offset and Dispersion Image

[Optimum Offset and Dispersion Image](https://www.masw.com/OptimumOffsetDispersion.html)

[[12]](https://file.scirp.org/Html/1-1211073_84426.htm#:~:text=The%20Common%20Midpoint%20%28CMP%29%20cross,squares%20approach%20%5B31%5D) [[13]](https://file.scirp.org/Html/1-1211073_84426.htm#:~:text=gathers%20is%20as%20follows%3A%20First%2C,are%20stacked%20in%20time%20domain) [[14]](https://file.scirp.org/Html/1-1211073_84426.htm#:~:text=gathers%20is%20as%20follows%3A%20First%2C,correlation) [[15]](https://file.scirp.org/Html/1-1211073_84426.htm#:~:text=gathers%20is%20as%20follows%3A%20First%2C,utilized%20to%20obtain%20inversion%20of) [[16]](https://file.scirp.org/Html/1-1211073_84426.htm#:~:text=4) [[17]](https://file.scirp.org/Html/1-1211073_84426.htm#:~:text=provided%20by%20genetic%20algorithm%20,Figure%206) [[19]](https://file.scirp.org/Html/1-1211073_84426.htm#:~:text=4) MASW Survey with Fixed Receiver Geometry and CMP Cross-Correlation
Technique for Data Processing: A Case Study of Wadi Fatima, Western Saudi
Arabia

[MASW Survey with Fixed Receiver Geometry and CMP Cross-Correlation Technique for Data Processing: A Case Study of Wadi Fatima, Western Saudi Arabia](https://file.scirp.org/Html/1-1211073_84426.htm)

[[18]](https://www.crewes.org/Documents/ResearchReports/2019/CRR201946.pdf#:~:text=techniques%20%28Thom,2019) [[20]](https://www.crewes.org/Documents/ResearchReports/2019/CRR201946.pdf#:~:text=techniques%20%28Thom,2019) Comparison of different surface wave inversion methods in engineering
scale

https://www.crewes.org/Documents/ResearchReports/2019/CRR201946.pdf

[[21]](https://www.researchgate.net/publication/364772217_DAS_for_2D_MASW_Imaging_A_Case_Study_on_the_Benefits_of_Flexible_Sub-Array_Processing) [[22]](https://www.researchgate.net/publication/364772217_DAS_for_2D_MASW_Imaging_A_Case_Study_on_the_Benefits_of_Flexible_Sub-Array_Processing#:~:text=of%20shear,subsurface%20%20layering%20%20and) [[23]](https://www.researchgate.net/publication/364772217_DAS_for_2D_MASW_Imaging_A_Case_Study_on_the_Benefits_of_Flexible_Sub-Array_Processing#:~:text=2D%20MASW%20results%20at%20a,study%20site%20and%20evaluate%20those) (PDF) DAS for 2D MASW Imaging: A Case Study on the Benefits of
Flexible Sub-Array Processing

https://www.researchgate.net/publication/364772217_DAS_for_2D_MASW_Imaging_A_Case_Study_on_the_Benefits_of_Flexible_Sub-Array_Processing
